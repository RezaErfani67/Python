import asyncio
from typing import Optional, List, Dict, Any, cast
from dataclasses import dataclass, field, replace
import flet as ft

from sqlmodel import SQLModel, Field, Relationship, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import func

# 1. Observable Store
@dataclass
@ft.observable
class PostStore:
    posts: List["PostDTO"] = field(default_factory=list)
    loading: bool = False
    error: str = ""
    editing_post_id: Optional[int] = None
    editing_post_data: Optional["PostDTO"] = None
    page: int = 1
    page_size: int = 5
    total: int = 0

    async def next_page(self):
        if self.page * self.page_size < self.total:
            self.page += 1
            await self.load_posts()

    async def prev_page(self):
        if self.page > 1:
            self.page -= 1
            await self.load_posts()

    async def load_posts(self):
        self.loading = True
        self.error = ""
        try:
            result = await get_posts_page(self.page, self.page_size)

            self.total = result["total"]

            self.posts = [
                PostDTO(
                    id=p.id,
                    title=p.title,
                    content=p.content,
                    user_id=p.user_id,
                    comments=[
                        CommentDTO(id=c.id, content=c.content)
                        for c in p.comments
                    ],
                )
                for p in result["items"]
            ]

        except Exception as e:
            self.error = f"Error loading posts: {e}"
        finally:
            self.loading = False


    
    def start_editing(self, post_id: int):
        self.editing_post_id = post_id
        for post in self.posts:
            if post.id == post_id:
                self.editing_post_data = replace(post)
                break
    
    def update_editing_post(self, title: str, content: str):
        if self.editing_post_data:
            self.editing_post_data.title = title
            self.editing_post_data.content = content
    
    async def save_editing_post(self) -> bool:
        if not self.editing_post_data or not self.editing_post_id:
            return False
        
        try:
            updated_post = await update_post(
                self.editing_post_id,
                self.editing_post_data.title,
                self.editing_post_data.content
            )
            
            if updated_post:
                for i, post in enumerate(self.posts):
                    if post.id == self.editing_post_id:
                        self.posts[i] = updated_post
                        break
                
                self.editing_post_id = None
                self.editing_post_data = None
                return True
        
        except Exception as e:
            self.error = f"Error saving post: {e}"
        
        return False
    
    def cancel_editing(self):
        self.editing_post_id = None
        self.editing_post_data = None


@dataclass
@ft.observable
class PostDTO:
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    user_id: int = 0
    comments: List["CommentDTO"] = field(default_factory=list)


@dataclass
@ft.observable
class CommentDTO:
    id: int
    content: str


# 2. Create global store instance
post_store = PostStore()


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int = Field(default=None, primary_key=True)
    username: str = Field(default="", unique=True)
    posts: List["Post"] = Relationship(back_populates="user")


class Post(SQLModel, table=True):
    __tablename__ = "posts"
    id: int = Field(default=None, primary_key=True)
    title: str = Field()
    user_id: int = Field(foreign_key="users.id")
    content: str = Field()
    user: Optional[User] = Relationship(back_populates="posts")
    comments: List["Comment"] = Relationship(back_populates="post")


class Comment(SQLModel, table=True):
    __tablename__ = "comments"
    id: int = Field(default=None, primary_key=True)
    content: str = Field()
    post_id: int = Field(foreign_key="posts.id")
    post: Optional[Post] = Relationship(back_populates="comments")


DATABASE_URL = "postgresql+asyncpg://postgres:1@127.0.0.1:5432/automation"
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_posts_page(page: int, page_size: int) -> Dict[str, Any]:
    offset = (page - 1) * page_size

    async with SessionLocal() as session:
        total = await session.scalar(
            select(func.count(Post.id))
        )

        result = await session.execute(
            select(Post)
            .options(selectinload(Post.user))
            .options(selectinload(Post.comments))
            .order_by(Post.id.desc())
            .limit(page_size)
            .offset(offset)
        )

        return {
            "items": result.scalars().unique().all(),
            "total": total,
        }


async def get_all_posts():
    async with SessionLocal() as session:
        result = await session.execute(
            select(Post)
            .options(selectinload(Post.user))
            .options(selectinload(Post.comments))
        )
        posts = result.scalars().all()
        return posts


async def get_post_by_id(post_id: int) -> Optional[PostDTO]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Post)
            .where(Post.id == post_id)
            .options(selectinload(Post.user))
            .options(selectinload(Post.comments))
        )
        post = result.scalars().first()

        if post:
            return PostDTO(
                id=post.id,
                title=post.title,
                user_id=post.user_id,
                content=post.content,
                comments=[CommentDTO(id=c.id, content=c.content) for c in post.comments]
            )
        else:
            print(f"Post with id={post_id} not found.")
            return None


async def update_post(post_id: int, title: str, content: str) -> Optional[PostDTO]:
    async with SessionLocal() as session:
        try:
            result = await session.execute(select(Post).where(Post.id == post_id))
            post = result.scalars().first()

            if not post:
                print(f"Post with id={post_id} not found for update.")
                return None

            post.title = title
            post.content = content

            await session.commit()
            await session.refresh(post)

            print(f"Post updated successfully with id={post.id}")

            result = await session.execute(
                select(Post)
                .where(Post.id == post_id)
                .options(selectinload(Post.comments))
            )
            updated_post = result.scalars().first()

            return PostDTO(
                id=updated_post.id,
                title=updated_post.title,
                user_id=updated_post.user_id,
                content=updated_post.content,
                comments=[CommentDTO(id=c.id, content=c.content) for c in updated_post.comments]
            )

        except Exception as e:
            print(f"Error updating post: {e}")
            await session.rollback()
            return None


# 3. کامپوننت برای نمایش کامنت‌ها
@ft.component
def CommentsView(comments: List[CommentDTO]):
    if not comments:
        return ft.Text("No comments yet", italic=True, color=ft.Colors.GREY_500)
    
    return ft.Column(
        controls=[
            ft.Text("Comments:", weight=ft.FontWeight.BOLD),
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(f"#{i+1}: {comment.content}"),
                        padding=ft.Padding.only(left=20, top=5, bottom=5),
                        border=ft.Border.all(1, ft.Colors.GREY_300),
                        border_radius=5,
                        margin=ft.Margin.only(bottom=5),
                    )
                    for i, comment in enumerate(comments)
                ],
                spacing=5,
            )
        ],
        spacing=10,
    )


# 4. کامپوننت برای ویرایش پست
@ft.component
def EditPost():
    store_state, _ = ft.use_state(post_store)
    
    if not store_state.editing_post_data:
        return ft.Text("No post selected for editing", italic=True)
    
    post = store_state.editing_post_data
    
    def update_title(e):
        store_state.update_editing_post(
            title=e.control.value,
            content=post.content
        )
    
    def update_content(e):
        store_state.update_editing_post(
            title=post.title,
            content=e.control.value
        )
    
    return ft.Column(
        controls=[
            ft.TextField(
                label="Title",
                value=post.title if post else "",
                on_change=update_title,
                width=400
            ),
            ft.TextField(
                label="Content",
                value=post.content if post else "",
                on_change=update_content,
                multiline=True,
                min_lines=5,
                width=400
            ),
        ],
        spacing=15,
    )


# 5. کامپوننت ردیف پست
@ft.component
def PostRow(post: PostDTO):
    store_state, _ = ft.use_state(post_store)
    dlg_edit_ref = ft.use_ref(cast(Optional[ft.AlertDialog], None))
    
    # State برای نمایش/مخفی کردن کامنت‌ها
    show_comments, set_show_comments = ft.use_state(False)

    async def handle_save(e):
        success = await store_state.save_editing_post()
        
        if success:
            e.page.pop_dialog()
            success_dialog = ft.AlertDialog(
                title=ft.Text("Success"),
                content=ft.Text("Post updated successfully!"),
                actions=[ft.TextButton("OK", on_click=lambda e: e.page.pop_dialog())]
            )
            e.page.show_dialog(success_dialog)
        else:
            error_dialog = ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text("Failed to update post!"),
                actions=[ft.TextButton("OK", on_click=lambda e: e.page.pop_dialog())]
            )
            e.page.show_dialog(error_dialog)

    def handle_cancel(e):
        store_state.cancel_editing()
        e.page.pop_dialog()

    def create_dialog():
        return ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Post"),
            content=EditPost(),
            actions=[
                ft.TextButton("Save", on_click=handle_save),
                ft.TextButton("Cancel", on_click=handle_cancel)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    if dlg_edit_ref.current is None:
        dlg_edit_ref.current = create_dialog()

    def open_edit_dialog():
        store_state.start_editing(post.id)
        
        if dlg_edit_ref.current is None:
            dlg_edit_ref.current = create_dialog()
        
        if dlg_edit_ref.current:
            ft.context.page.show_dialog(dlg_edit_ref.current)
    
    def toggle_comments():
        set_show_comments(not show_comments)
    
    return ft.Column(
        controls=[
            # ردیف اصلی پست
            ft.Row(
                spacing=20,
                controls=[
                    ft.Text(str(post.id), width=50),
                    ft.Column(
                        controls=[
                            ft.Text(post.title, weight=ft.FontWeight.BOLD),
                            ft.Text(post.content[:100] + "..." if len(post.content) > 100 else post.content, 
                                   size=12, color=ft.Colors.GREY_600),
                        ],
                        expand=True,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(f"Comments: {len(post.comments)}", size=12),
                            ft.Text(f"User ID: {post.user_id}", size=12),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                    ),
                ],
            ),
            
            # دکمه‌های اکشن
            ft.Row(
                spacing=10,
                controls=[
                    ft.Button(
                        "Edit Post",
                        on_click=open_edit_dialog,
                        icon=ft.Icons.EDIT,
                    ),
                    ft.Button(
                        "Show Comments" if not show_comments else "Hide Comments",
                        on_click=toggle_comments,
                        icon=ft.Icons.COMMENT,
                    ),
                ],
            ),
            
            # نمایش کامنت‌ها (اگر show_comments True باشد)
            CommentsView(post.comments) if show_comments else ft.Container(),
            
            # خط جداکننده
            ft.Divider(height=1, color=ft.Colors.GREY_300),
        ],
        spacing=15,
    )

@ft.component
def PaginationBar():
    store, _ = ft.use_state(post_store)

    total_pages = max(1, (store.total + store.page_size - 1) // store.page_size)

    return ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
        controls=[
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                disabled=store.page == 1,
                on_click=lambda e: asyncio.create_task(store.prev_page()),
            ),
            ft.Text(f"Page {store.page} / {total_pages}"),
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                disabled=store.page == total_pages,
                on_click=lambda e: asyncio.create_task(store.next_page()),
            ),
        ],
    )


# 6. کامپوننت اصلی اپلیکیشن
@ft.component
def App():
    store_state, _ = ft.use_state(post_store)



    
    
    # لود اولیه پست‌ها
    def effect():
        async def load():
            await store_state.load_posts()
        asyncio.create_task(load())
    
    #ft.use_effect(effect, [])
    ft.use_effect(effect, [store_state.page])

    if store_state.loading:
        return ft.Column(
            controls=[
                ft.ProgressBar(),
                ft.Text("Loading posts...")
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )
    
    if store_state.error:
        return ft.Column(
            controls=[
                ft.Text("Error:", weight=ft.FontWeight.BOLD),
                ft.Text(store_state.error, color=ft.Colors.RED),
                ft.Button(
                    "Retry",
                    on_click=lambda e: asyncio.create_task(store_state.load_posts()),
                    icon=ft.Icons.REFRESH,
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )
    
    return ft.Column(
        controls=[
            # هدر
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text("📝 Blog Posts", size=28, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            on_click=lambda e: asyncio.create_task(store_state.load_posts()),
                            tooltip="Refresh posts",
                            icon_size=30,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.Padding.only(bottom=20),
            ),
            
            # لیست پست‌ها
            ft.Container(
            expand=True,
            content=ft.ListView(
                controls=[PostRow(post) for post in store_state.posts],
                spacing=25,
                padding=20,
            ),
        ),

            PaginationBar(),

            
            
            # پاورقی
            ft.Container(
                content=ft.Text(
                    f"Total posts: {len(store_state.posts)} | "
                    f"Total comments: {sum(len(post.comments) for post in store_state.posts)}",
                    size=12,
                    color=ft.Colors.GREY_500,
                ),
                padding=ft.Padding.only(top=20),
                alignment=ft.Alignment.CENTER,
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
    )


# 7. تابع اصلی
async def main(page: ft.Page):
    page.title = "Blog App"
    page.window.center()
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    #page.window.maximized = True
    page.window.maximizable = True
    page.window.minimizable = True
    page.window.center()
    page.window.frameless=False
    page.theme_mode = ft.ThemeMode.LIGHT
    page.Padding = 30
    page.scroll = ft.ScrollMode.AUTO
    page.theme = ft.Theme(
        font_family="Vazirmatn, Arial, sans-serif",
        color_scheme_seed=ft.Colors.BLUE,
    )
    
    # استایل‌های اضافی
    page.theme.page_transitions.windows = "cupertino"
    page.theme.page_transitions.macos = "cupertino"
    page.theme.page_transitions.linux = "cupertino"
    
    loading_text = ft.Text("Initializing database...")
    page.add(loading_text)
    
    try:
        page.clean()
        page.render(App)
    except Exception as e:
        page.clean()
        page.add(ft.Text(f"Database error: {e}", color=ft.Colors.RED))


if __name__ == "__main__":
    ft.app(target=main)
