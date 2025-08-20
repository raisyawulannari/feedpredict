<template>
  <div class="home-container">
    <!-- Header dengan gambar full dan overlay teks -->
    <div class="header-banner">
      <img src="../assets/home-ayam.jpg" alt="Ayam Peternakan" class="banner-image" />
      <div class="banner-overlay">
        <h1>Selamat Datang di <span class="highlight">FEED PREDICT</span></h1>
      </div>
    </div>

    <!-- Tentang Feed Predict (Split 2 kolom) -->
    <section class="about-section">
      <div class="about-text">
        <h2>📢 Apa Itu Feed Predict?</h2>
        <p>
          Feed Predict adalah aplikasi prediksi kebutuhan pakan ayam broiler menggunakan metode statistik ARIMA.
          Dengan analisis data harian, aplikasi ini membantu peternak menentukan jumlah pakan optimal setiap hari,
          menghindari pemborosan dan kekurangan pakan.
        </p>
        <ul>
          <li>✔️ Efisiensi Pakan</li>
          <li>✔️ Prediksi Akurat</li>
          <li>✔️ Data Harian Otomatis</li>
        </ul>
      </div>
      <div class="about-image">
        <img src="../assets/home2.avif" alt="Ayam" />
      </div>
    </section>

    <!-- Info ARIMA dalam kotak hijau -->
    <section class="arima-info">
      <h2>📊 Apa Itu Metode ARIMA?</h2>
      <p>
        ARIMA (Autoregressive Integrated Moving Average) adalah metode statistik untuk memprediksi data berdasarkan tren
        historis.
        Feed Predict menggunakan ARIMA untuk menghitung kebutuhan pakan harian ayam broiler berdasarkan pola konsumsi
        sebelumnya.
      </p>

      <!-- Tombol Login/Register jika belum login -->
      <div class="arima-buttons">
        <router-link v-if="!isLoggedIn" to="/login" class="prediksi-btn">Login</router-link>
        <router-link v-if="!isLoggedIn" to="/register" class="prediksi-btn">Register</router-link>
        <!-- Bisa tambahkan tombol lain jika user sudah login -->
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const isLoggedIn = ref(false)

onMounted(() => {
  isLoggedIn.value = !!localStorage.getItem('token')
})
</script>

<style scoped>
.home-container {
  font-family: 'Segoe UI', sans-serif;
  color: #333;
}

/* Header full dengan overlay */
.header-banner {
  position: relative;
  width: 100%;
  height: 300px;
  overflow: hidden;
}

.banner-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: brightness(70%);
}

.banner-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.8);
  font-size: 1.8rem;
}

.highlight {
  color: #3e8a0b;
  font-weight: bold;
}

/* Tentang Feed Predict (split 2) */
.about-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 30px 20px;
}

.about-text {
  flex: 1;
}

.about-text h2 {
  color: #3e8a0b;
  margin-bottom: 10px;
}

.about-text p {
  font-size: 1rem;
  line-height: 1.5;
}

.about-text ul {
  margin-top: 10px;
  list-style: none;
  padding-left: 0;
}

.about-text li {
  margin-bottom: 5px;
  font-size: 0.95rem;
}

.about-image {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.about-image img {
  width: 80%;
  max-width: 400px;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

/* Responsive split */
@media (min-width: 768px) {
  .about-section {
    flex-direction: row;
  }
}

/* ARIMA Info Box */
.arima-info {
  background-color: #3e8a0b;
  color: white;
  padding: 30px 20px;
  text-align: center;
  margin-top: 30px;
}

.arima-info h2 {
  margin-bottom: 15px;
}

.arima-info p {
  font-size: 1rem;
  line-height: 1.5;
  max-width: 800px;
  margin: auto;
}

.arima-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.prediksi-btn {
  display: inline-block;
  background-color: white;
  color: #3e8a0b;
  font-weight: bold;
  padding: 10px 20px;
  border-radius: 8px;
  text-decoration: none;
  transition: background-color 0.3s ease, color 0.3s ease, transform 0.2s ease;
}

.prediksi-btn:hover {
  background-color: #2f6a08;
  color: white;
  transform: scale(1.05);
}
</style>
