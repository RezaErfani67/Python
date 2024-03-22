<template>
  <div>
    <h1>Matplotlib Plot</h1>
    <div class="grid grid-cols-6 gap-2">
      <div class="flex flex-col gap-4">
        <button @click="zoomIn" class="btn btn-primary">Zoom In</button>
        <button @click="zoomOut" class="btn btn-primary">Zoom Out</button>
      </div>
      <div class="col-span-4 self-center border">
        <img :src="plotUrl" alt="Matplotlib Plot" />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      plotUrl: "",
      xRange: [0, 10], // Initial x-range (example values)
      yRange: [0, 20], // Initial y-range (example values)
      socket: null,
    };
  },
  mounted() {
    this.setupWebSocket();
  },
  methods: {
    setupWebSocket() {
      // this.socket = new WebSocket(`ws://localhost:8000/ws?x_range=${this.xRange}&y_range=${this.yRange}`);
      this.socket = new WebSocket("ws://localhost:8000/ws");

      this.socket.onopen = () => {
        console.log("WebSocket connection established");
        setInterval(() => {
          this.sendZoomParams(this.xRange, this.yRange);
        }, 1000);
      };
      this.socket.onmessage = (event) => {
        this.plotUrl = `data:image/png;base64,${event.data}`;
      };
    },
    zoomIn() {
      // Adjust the xRange and yRange accordingly
      this.xRange = [this.xRange[0] * 0.9, this.xRange[1] * 0.9];
      this.yRange = [this.yRange[0] * 0.9, this.yRange[1] * 0.9];
      this.sendZoomParams(this.xRange, this.yRange);
    },
    zoomOut() {
      // Adjust the xRange and yRange accordingly
      this.xRange = [this.xRange[0] * 1.1, this.xRange[1] * 1.1];
      this.yRange = [this.yRange[0] * 1.1, this.yRange[1] * 1.1];
      this.sendZoomParams(this.xRange, this.yRange);
    },

    sendZoomParams(xRange, yRange) {
      if (this.socket.readyState === WebSocket.OPEN) {
        const zoomParams = { x_range: xRange, y_range: yRange };
        this.socket.send(JSON.stringify(zoomParams));
      }
    },
  },
  beforeDestroy() {
    if (this.socket) {
      this.socket.close();
    }
  },
};
</script>
