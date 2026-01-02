import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import time

import flet as ft

from sqlmodel import SQLModel, Field, Relationship, select
from sqlalchemy import Column, DateTime, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import selectinload

# =====================================================
# DATABASE
# =====================================================

DATABASE_URL = "postgresql+asyncpg://postgres:1@127.0.0.1:5432/automation"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# =====================================================
# MODELS
# =====================================================

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)

    interests: List[dict] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default="[]"),
    )

    posts: List["Post"] = Relationship(back_populates="user")


class Post(SQLModel, table=True):
    __tablename__ = "posts"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    content: str
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True))
    )
    user_id: int = Field(foreign_key="users.id")
    user: Optional[User] = Relationship(back_populates="posts")
    comments: List["Comment"] = Relationship(back_populates="post")


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(max_length=500)
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True))
    )
    post_id: int = Field(foreign_key="posts.id")
    post: Optional[Post] = Relationship(back_populates="comments")

# =====================================================
# MIGRATION FUNCTIONS
# =====================================================

async def check_and_add_columns():
    """ستون‌های created_at رو به جداول موجود اضافه می‌کنه"""
    async with engine.begin() as conn:
        # بررسی وجود ستون created_at در جدول posts
        result = await conn.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'posts' AND column_name = 'created_at'
            """)
        )
        posts_has_column = result.scalar() is not None
        
        # بررسی وجود ستون created_at در جدول comments
        result = await conn.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'comments' AND column_name = 'created_at'
            """)
        )
        comments_has_column = result.scalar() is not None
        
        # اگر ستون‌ها وجود ندارن، اضافه می‌کنیم
        if not posts_has_column:
            print("Adding created_at column to posts table...")
            await conn.execute(
                text("ALTER TABLE posts ADD COLUMN created_at TIMESTAMP WITH TIME ZONE")
            )
        
        if not comments_has_column:
            print("Adding created_at column to comments table...")
            await conn.execute(
                text("ALTER TABLE comments ADD COLUMN created_at TIMESTAMP WITH TIME ZONE")
            )
        
        await conn.commit()
        print("Migration completed successfully!")


async def init_db():
    """ایجاد جداول و اجرای migration"""
    try:
        # ابتدا جداول رو ایجاد می‌کنیم
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        print("Tables created successfully")
        
        # سپس migration رو اجرا می‌کنیم
        await check_and_add_columns()
        
    except Exception as e:
        print(f"Error in database initialization: {e}")
        # اگر خطا داد، فقط migration رو اجرا می‌کنیم
        try:
            await check_and_add_columns()
        except Exception as e2:
            print(f"Migration also failed: {e2}")

# =====================================================
# SERVICES
# =====================================================

async def login_user(username: str) -> dict:
    async with SessionLocal() as s:
        res = await s.execute(select(User).where(User.username == username))
        user = res.scalar_one_or_none()

        if not user:
            user = User(username=username)
            s.add(user)
            await s.commit()
            await s.refresh(user)

        return {
            'id': user.id,
            'username': user.username
        }


async def create_post(user_id: int, title: str, content: str) -> dict:
    async with SessionLocal() as s:
        try:
            print(f"Creating post with user_id={user_id}, title={title}")
            post = Post(title=title, content=content, user_id=user_id)
            s.add(post)
            await s.commit()
            await s.refresh(post)
            
            print(f"Post created successfully with id={post.id}")
            
            post_dict = {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'user_id': post.user_id,
                'created_at': post.created_at.isoformat() if post.created_at else None,
                'comments': []
            }
            return post_dict
        except Exception as e:
            print(f"Error creating post: {e}")
            return {}


async def create_comment(post_id: int, content: str) -> dict:
    async with SessionLocal() as session:
        try:
            print(f"Creating comment for post_id={post_id}, content={content}")
            comment = Comment(post_id=post_id, content=content)
            session.add(comment)
            await session.commit()
            await session.refresh(comment)
            
            print(f"Comment created successfully with id={comment.id}")
            
            comment_dict = {
                'id': comment.id,
                'content': comment.content,
                'post_id': comment.post_id,
                'created_at': comment.created_at.isoformat() if comment.created_at else None
            }
            return comment_dict
        except Exception as e:
            print(f"Error creating comment: {e}")
            return {}


async def load_all_posts_with_comments() -> List[dict]:
    async with SessionLocal() as s:
        try:
            res = await s.execute(
                select(Post)
                .options(selectinload(Post.comments))
                .order_by(Post.id.desc())
            )
            posts = res.scalars().all()
            
            post_dicts = []
            for post in posts:
                comment_dicts = []
                for comment in post.comments:
                    comment_dicts.append({
                        'id': comment.id,
                        'content': comment.content,
                        'post_id': comment.post_id,
                        'created_at': comment.created_at.isoformat() if comment.created_at else None
                    })
                
                post_dicts.append({
                    'id': post.id,
                    'title': post.title,
                    'content': post.content,
                    'user_id': post.user_id,
                    'created_at': post.created_at.isoformat() if post.created_at else None,
                    'comments': comment_dicts
                })
            
            print(f"Loaded {len(post_dicts)} posts")
            return post_dicts
        except Exception as e:
            print(f"Error loading posts: {e}")
            return []


async def load_comments_for_post(post_id: int) -> List[dict]:
    """بارگذاری کامنت‌های یک پست خاص"""
    async with SessionLocal() as s:
        try:
            print(f"Loading comments for post_id={post_id}")
            # ابتدا پست را با کامنت‌هایش پیدا می‌کنیم
            res = await s.execute(
                select(Post)
                .options(selectinload(Post.comments))
                .where(Post.id == post_id)
            )
            post = res.scalar_one_or_none()
            
            if not post:
                print(f"Post {post_id} not found")
                return []
            
            # کامنت‌ها را به فرمت مناسب تبدیل می‌کنیم
            comment_dicts = []
            for comment in post.comments:
                comment_dicts.append({
                    'id': comment.id,
                    'content': comment.content,
                    'post_id': comment.post_id,
                    'created_at': comment.created_at.isoformat() if comment.created_at else None
                })
            
            print(f"Loaded {len(comment_dicts)} comments for post {post_id}")
            return comment_dicts
        except Exception as e:
            print(f"Error loading comments for post {post_id}: {e}")
            return []

# =====================================================
# UI COMPONENTS
# =====================================================

@ft.component
def Login(on_login):
    username, set_username = ft.use_state("")
    error, set_error = ft.use_state("")
    loading, set_loading = ft.use_state(False)

    async def submit():
        if not username.strip():
            set_error("Username required")
            return
        
        set_loading(True)
        set_error("")
        try:
            user = await login_user(username.strip())
            on_login(user)
        except Exception as e:
            set_error(str(e))
        finally:
            set_loading(False)

    return ft.Container(
        width=400,
        height=300,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        padding=20,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.BLACK12,
        ),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            controls=[
                ft.Icon(ft.Icons.PERSON, size=40, color=ft.Colors.BLUE),
                ft.Text("Welcome to Blog", size=24, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    label="Username",
                    value=username,
                    autofocus=True,
                    width=300,
                    on_submit=lambda e: asyncio.create_task(submit()),
                    on_change=lambda e: set_username(e.control.value),
                    filled=True,
                    border_radius=8,
                ),
                ft.ElevatedButton(
                    "Login / Register",
                    on_click=lambda e: asyncio.create_task(submit()),
                    width=300,
                    height=45,
                    disabled=loading,
                ),
                ft.ProgressRing() if loading else ft.Container(),
                ft.Text(
                    error,
                    color=ft.Colors.RED,
                    size=12,
                    visible=bool(error)
                ),
            ],
        ),
    )


@ft.component
def CommentItem(comment_data: dict):
    if not isinstance(comment_data, dict):
        comment_data = {}
    
    content = comment_data.get('content', '')
    created_at = comment_data.get('created_at', '')
    
    time_display = ""
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            time_display = dt.strftime('%H:%M')
        except:
            time_display = ""
    
    return ft.Container(
        padding=ft.Padding(left=10, top=8, right=10, bottom=8),
        bgcolor=ft.Colors.GREY_50,
        border_radius=8,
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=16, color=ft.Colors.BLUE_700),
                ft.Column(
                    expand=True,
                    spacing=2,
                    controls=[
                        ft.Text(content, size=14),
                        ft.Text(
                            time_display,
                            size=10,
                            color=ft.Colors.GREY_500,
                        ) if time_display else ft.Container(),
                    ],
                ),
            ],
            spacing=10,
        ),
        margin=ft.Margin(bottom=5),
    )


@ft.component
def CommentSection(post_id: int, initial_comments: List[dict], on_comments_updated):
    """
    کامپوننت بخش کامنت‌ها
    post_id: ID پست مربوطه
    initial_comments: لیست اولیه کامنت‌ها
    on_comments_updated: callback برای اطلاع‌رسانی به parent
    """
    comment_text, set_comment_text = ft.use_state("")
    submitting, set_submitting = ft.use_state(False)
    comments, set_comments = ft.use_state(initial_comments or [])
    loading_comments, set_loading_comments = ft.use_state(False)
    
    # وقتی initial_comments تغییر کند، comments را به‌روز می‌کنیم
    ft.use_effect(lambda: set_comments(initial_comments or []), [initial_comments])
    
    async def handle_add_comment():
        if not comment_text.strip():
            return
        
        set_submitting(True)
        try:
            # کامنت جدید را ایجاد می‌کنیم
            new_comment = await create_comment(post_id, comment_text.strip())
            if new_comment and isinstance(new_comment, dict) and 'id' in new_comment:
                # کامنت جدید را به لیست اضافه می‌کنیم
                updated_comments = comments + [new_comment]
                set_comments(updated_comments)
                set_comment_text("")
                
                # به parent اطلاع می‌دهیم که کامنت‌ها به‌روز شده‌اند
                if on_comments_updated:
                    await on_comments_updated(updated_comments)
            else:
                print(f"Invalid comment data: {new_comment}")
                    
        except Exception as e:
            print(f"Error adding comment: {e}")
        finally:
            set_submitting(False)
    
    async def refresh_comments():
        """کامنت‌های این پست خاص را refresh می‌کند"""
        if loading_comments:
            return
        
        set_loading_comments(True)
        try:
            # فقط کامنت‌های این پست را لود می‌کنیم
            new_comments = await load_comments_for_post(post_id)
            set_comments(new_comments)
            
            # به parent اطلاع می‌دهیم
            if on_comments_updated:
                await on_comments_updated(new_comments)
                
        except Exception as e:
            print(f"Error refreshing comments: {e}")
        finally:
            set_loading_comments(False)
    
    # کامنت‌ها را مرتب می‌کنیم (قدیمی‌ترین اول)
    sorted_comments = sorted(
        comments,
        key=lambda x: x.get('created_at', '') or x.get('id', 0),
        reverse=False
    )
    
    comments_display = [
        CommentItem(comment_data=comment)
        for comment in sorted_comments
    ]
    
    return ft.Column(
        spacing=10,
        controls=[
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.COMMENT, size=18, color=ft.Colors.BLUE),
                    ft.Text(
                        f"Comments ({len(comments)})",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_size=16,
                        tooltip="Refresh comments",
                        on_click=lambda e: asyncio.create_task(refresh_comments()),
                        disabled=loading_comments,
                    ) if not loading_comments else ft.ProgressRing(height=16, width=16),
                ],
                spacing=8,
            ),
            
            ft.Column(
                controls=comments_display,
                spacing=5,
            ) if comments_display else ft.Container(
                padding=10,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=30, color=ft.Colors.GREY_400),
                        ft.Text("No comments yet", size=12, color=ft.Colors.GREY),
                    ],
                ),
            ),
            
            ft.Container(
                padding=ft.Padding(top=10, bottom=5),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.TextField(
                                    hint_text="Write a comment...",
                                    value=comment_text,
                                    on_change=lambda e: set_comment_text(e.control.value),
                                    expand=True,
                                    height=45,
                                    border_radius=8,
                                    filled=True,
                                    disabled=submitting,
                                    on_submit=lambda e: asyncio.create_task(handle_add_comment()),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.SEND,
                                    on_click=lambda e: asyncio.create_task(handle_add_comment()),
                                    tooltip="Add comment",
                                    disabled=submitting or not comment_text.strip(),
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                        bgcolor=ft.Colors.BLUE if comment_text.strip() else ft.Colors.GREY_300,
                                        color=ft.Colors.WHITE,
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            controls=[
                                ft.ProgressRing(height=16, width=16) if submitting else ft.Container(),
                                ft.Text(
                                    "Press Enter to submit",
                                    size=10,
                                    color=ft.Colors.GREY_500,
                                    italic=True,
                                ),
                            ],
                            spacing=5,
                        ),
                    ],
                ),
            ),
        ],
    )


@ft.component
def PostItem(post_data: dict, current_user_id: int, on_post_updated):
    """
    کامپوننت نمایش یک پست
    on_post_updated: callback برای اطلاع‌رسانی زمانی که کامنت‌های این پست تغییر کند
    """
    if not isinstance(post_data, dict):
        post_data = {}
    
    post_id = post_data.get('id', 0)
    title = post_data.get('title', 'No Title')
    content = post_data.get('content', 'No Content')
    created_at = post_data.get('created_at', '')
    initial_comments = post_data.get('comments', [])
    
    time_display = ""
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            time_display = dt.strftime('%Y-%m-%d %H:%M')
        except:
            time_display = ""
    else:
        time_display = "Recent"
    
    async def handle_comments_updated(updated_comments):
        """زمانی که کامنت‌های این پست به‌روز شدند فراخوانی می‌شود"""
        # به parent اطلاع می‌دهیم که کامنت‌های این پست به‌روز شده‌اند
        updated_post_data = {**post_data, 'comments': updated_comments}
        if on_post_updated:
            await on_post_updated(post_id, updated_post_data)
    
    return ft.Container(
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.GREY_300,
        ),
        content=ft.Column(
            spacing=15,
            controls=[
                ft.Column(
                    spacing=5,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(title, size=20, weight=ft.FontWeight.BOLD, expand=True),
                                ft.Icon(ft.Icons.PERSON_OUTLINE, size=18, color=ft.Colors.GREY),
                            ],
                        ),
                        ft.Text(
                            time_display,
                            size=12,
                            color=ft.Colors.GREY_500,
                        ),
                    ],
                ),
                
                ft.Container(
                    padding=ft.Padding(left=5, top=5, bottom=10),
                    content=ft.Text(content, size=15),
                ),
                
                CommentSection(
                    post_id=post_id,
                    initial_comments=initial_comments,
                    on_comments_updated=handle_comments_updated
                ),
                
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.FAVORITE_BORDER,
                            icon_size=20,
                            tooltip="Like",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SHARE,
                            icon_size=20,
                            tooltip="Share",
                        ),
                    ],
                    spacing=5,
                ),
            ],
        ),
        margin=ft.Margin(bottom=20),
    )


@ft.component
def Blog(user_data: dict):
    if not isinstance(user_data, dict):
        user_data = {}
    
    user_id = user_data.get('id', 0)
    username = user_data.get('username', 'Unknown')
    
    # اطمینان حاصل کنیم که posts همیشه یک لیست است
    posts, set_posts = ft.use_state([])
    title, set_title = ft.use_state("")
    content, set_content = ft.use_state("")
    loading, set_loading = ft.use_state(False)
    creating_post, set_creating_post = ft.use_state(False)
    
    async def refresh_all_posts():
        """بارگذاری تمام پست‌ها (فقط در موارد ضروری)"""
        if loading:
            return
        
        set_loading(True)
        try:
            all_posts = await load_all_posts_with_comments()
            # اطمینان حاصل کنیم که all_posts یک لیست است
            if not isinstance(all_posts, list):
                print(f"Warning: load_all_posts_with_comments returned {type(all_posts)} instead of list")
                all_posts = []
            set_posts(all_posts)
        except Exception as e:
            print(f"Error refreshing posts: {e}")
            set_posts([])  # در صورت خطا لیست خالی قرار می‌دهیم
        finally:
            set_loading(False)
    
    async def handle_post_updated(post_id: int, updated_post_data: dict):
        """زمانی که یک پست خاص به‌روز می‌شود"""
        # فقط پست مورد نظر را در لیست به‌روز می‌کنیم
        def update_posts_list(prev_posts):
            # اطمینان حاصل کنیم که prev_posts یک لیست است
            if not isinstance(prev_posts, list):
                print(f"Warning: prev_posts is {type(prev_posts)}, converting to list")
                prev_posts = []
            
            updated_posts = []
            for post in prev_posts:
                # بررسی کنیم که post یک dictionary است
                if isinstance(post, dict) and post.get('id') == post_id:
                    updated_posts.append(updated_post_data)
                else:
                    updated_posts.append(post)
            return updated_posts
        set_posts(update_posts_list)
    
    async def submit_post():
        title_str = str(title) if title is not None else ""
        content_str = str(content) if content is not None else ""
        
        if not title_str.strip() or not content_str.strip():
            return
        
        set_creating_post(True)
        try:
            new_post = await create_post(user_id, title_str.strip(), content_str.strip())
            if new_post and isinstance(new_post, dict) and 'id' in new_post:
                # پست جدید را به ابتدای لیست اضافه می‌کنیم
                def add_new_post(prev_posts):
                    # اطمینان حاصل کنیم که prev_posts یک لیست است
                    if not isinstance(prev_posts, list):
                        print(f"Warning: prev_posts is {type(prev_posts)}, converting to list")
                        prev_posts = []
                    return [new_post] + prev_posts
                set_posts(add_new_post)
                set_title("")
                set_content("")
                print(f"Post added successfully: {new_post['title']}")
            else:
                print(f"Failed to create post or invalid post data: {new_post}")
        except Exception as e:
            print(f"Error creating post: {e}")
            import traceback
            traceback.print_exc()  # جزئیات خطا را چاپ می‌کند
        finally:
            set_creating_post(False)
    
    def is_form_valid():
        title_str = str(title) if title is not None else ""
        content_str = str(content) if content is not None else ""
        return bool(title_str.strip()) and bool(content_str.strip())
    
    # فقط یکبار در ابتدا پست‌ها را لود می‌کنیم
    ft.use_effect(lambda: asyncio.create_task(refresh_all_posts()), [])
    
    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=15,
                bgcolor=ft.Colors.BLUE,
                border_radius=10,
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.RSS_FEED, color=ft.Colors.WHITE),
                        ft.Text(
                            f"Welcome, {username}!",
                            size=22,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            icon_color=ft.Colors.WHITE,
                            tooltip="Refresh all posts",
                            on_click=lambda e: asyncio.create_task(refresh_all_posts()),
                            disabled=loading,
                        ),
                    ],
                    spacing=15,
                ),
                margin=ft.Margin(bottom=20),
            ),
            
            ft.Container(
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=10,
                    color=ft.Colors.GREY_300,
                ),
                content=ft.Column(
                    spacing=15,
                    controls=[
                        ft.Text("Create New Post", size=18, weight=ft.FontWeight.BOLD),
                        ft.TextField(
                            label="Title",
                            value=title,
                            on_change=lambda e: set_title(e.control.value),
                            autofocus=True,
                            border_radius=8,
                            filled=True,
                            disabled=creating_post,
                        ),
                        ft.TextField(
                            label="Content",
                            value=content,
                            multiline=True,
                            min_lines=4,
                            max_lines=8,
                            on_change=lambda e: set_content(e.control.value),
                            border_radius=8,
                            filled=True,
                            disabled=creating_post,
                        ),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Publish Post",
                                    on_click=lambda e: asyncio.create_task(submit_post()),
                                    disabled=creating_post or not is_form_valid(),
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    ),
                                    icon=ft.Icons.SEND,
                                ),
                                ft.ProgressRing() if creating_post else ft.Container(),
                            ],
                            spacing=15,
                        ),
                    ],
                ),
                margin=ft.Margin(bottom=25),
            ),
            
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LIST, color=ft.Colors.BLUE),
                            ft.Text("Recent Posts", size=18, weight=ft.FontWeight.BOLD),
                            ft.ProgressRing(height=20, width=20) if loading else ft.Container(),
                        ],
                        spacing=10,
                    ),
                    
                    ft.Column(
                        controls=[
                            PostItem(
                                post_data=post,
                                current_user_id=user_id,
                                on_post_updated=handle_post_updated
                            )
                            for post in posts
                        ],
                        spacing=10,
                    ) if posts else ft.Container(
                        padding=40,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=15,
                            controls=[
                                ft.Icon(ft.Icons.POST_ADD, size=60, color=ft.Colors.GREY_400),
                                ft.Text("No posts yet", size=16, color=ft.Colors.GREY),
                                ft.Text(
                                    "Be the first to share something!",
                                    size=14,
                                    color=ft.Colors.GREY_500,
                                ),
                            ],
                        ),
                    ),
                ],
                spacing=15,
            ),
        ],
        spacing=20,
    )

@ft.component
def App():
    user, set_user = ft.use_state(None)

    if not user:
        return Login(on_login=set_user)

    return Blog(user)


# =====================================================
# ENTRY POINT
# =====================================================

async def main(page: ft.Page):
    page.title = "Blog App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    page.theme = ft.Theme(
        font_family="Vazirmatn, Arial, sans-serif",
        color_scheme_seed=ft.Colors.BLUE,
    )
    
    # پیام loading
    loading_text = ft.Text("Initializing database...")
    page.add(loading_text)
    
    try:
        await init_db()
        page.clean()
        page.render(App)
    except Exception as e:
        page.clean()
        page.add(ft.Text(f"Database error: {e}", color=ft.Colors.RED))

if __name__ == "__main__":
    ft.app(target=main)
