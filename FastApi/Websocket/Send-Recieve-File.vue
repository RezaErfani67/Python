<template>
  <div>
    <h1>WebSocket Chat</h1>
    <div>
      <label for="room">Enter Room ID:</label>
      <input type="text" id="room" v-model="roomId" placeholder="Enter Room ID">
      <button @click="joinRoom">Join Room</button>
    </div>
    <div>
      <input type="file" id="fileInput" @change="onFileChange" accept="image/*">
      <button @click="sendImage">Send Image</button>
    </div>
    <div id="chat">
      <div v-for="(msg, index) in messages" :key="index">
        <template v-if="msg.type === 'text'">
          <p>{{ msg.username }}: {{ msg.text }}</p>
        </template>
        <template v-else-if="msg.type === 'image'">
          <img :src="msg.image" style="max-width: 300px; max-height: 300px;">
        </template>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      socket: null,
      roomId: '',
      messages: [],
      selectedFile: null
    };
  },
  methods: {
    joinRoom() {
      this.socket = new WebSocket(`ws://localhost:8000/ws/${this.roomId}`);
      this.socket.onmessage = this.handleMessage;
    },
    handleMessage(event) {
      const data = JSON.parse(event.data);
      this.messages.push(data);
    },
    onFileChange(event) {
      this.selectedFile = event.target.files[0];
    },
    async sendImage() {
      if (this.selectedFile) {
        const reader = new FileReader();
        reader.onload = async (event) => {
          const imageData = event.target.result;
          const imageMessage = {
            type: 'image',
            image: imageData
          };
          this.socket.send(JSON.stringify(imageMessage));
        };
        reader.readAsDataURL(this.selectedFile);
        this.selectedFile = null;
      }
    }
  }
};
</script>

<style scoped>
/* Add your CSS styles here */
</style>
