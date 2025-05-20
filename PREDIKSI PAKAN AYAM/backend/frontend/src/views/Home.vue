<template>
  <main class="main-content">
    <div class="content-wrapper">
      <h2 class="welcome">Selamat Datang di FEED PREDICT</h2>

      <div class="hero-image">
        <img src="../assets/home-ayam.jpg" alt="Ayam Peternakan" />
      </div>

      <div class="title">
        <h2>Sistem Prediksi Kebutuhan Pakan</h2>
        <h3 class="highlight">Ayam Pedaging Berbasis ARIMA</h3>
      </div>

      <p class="subtitle">
        “Untuk membantu perencanaan pakan secara lebih akurat dan efisien”
      </p>
      <div class="scroll-indicator">⌄</div>
    </div>
  </main>
</template>

<script setup>
// Tidak ada logic yang diperlukan di sini
</script>

<style scoped>
.main-content {
  width: 100%;
  display: flex;
  justify-content: center;
}

.content-wrapper {
  max-width: 800px;
  width: 100%;
  text-align: center;
}

.hero-image img {
  width: 100%;
  max-width: 600px;
  height: auto;
  margin: 2rem auto;
  display: block;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.welcome {
  font-weight: bold;
  color: #5d2d1d;
  margin-top: 1rem;
}

.title h2 {
  font-size: 2rem;
  color: #5d2d1d;
  margin-top: 1rem;
}

.highlight {
  font-size: 1.5rem;
  color: #7ca221;
}

.subtitle {
  font-style: italic;
  font-size: 1rem;
  color: #333;
  margin-top: 1rem;
}

.scroll-indicator {
  font-size: 2rem;
  margin-top: 1.5rem;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(8px);
  }
}
</style>
