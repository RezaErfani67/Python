<template>
  <div>
    <h1>Matplotlib Plot</h1>
    <img :src="plotUrl" alt="Matplotlib Plot">
  </div>
</template>

<script>
export default {
  data() {
    return {
      plotUrl: '',
    };
  },
  mounted() {
    this.setupWebSocket();
  },
  methods: {
    setupWebSocket() {
      const socket = new WebSocket('ws://localhost:8000/ws');
      socket.onmessage = (event) => {
        this.plotUrl = `data:image/png;base64,${event.data}`;
      };
    },
  },
};
</script>
