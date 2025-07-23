<template>
  <main class="main-content">
    <div class="content-wrapper">
      <h2 class="welcome">Selamat Datang di FEED PREDICT</h2>

      <div class="hero-image">
        <img src="../assets/home-ayam.jpg" alt="Ayam Peternakan" />
      </div>

                  
      <div class="scroll-indicator">⌄</div>

      <div class="title">
        <h2>Sistem Prediksi Kebutuhan Pakan</h2>
        <h3 class="highlight">Ayam Pedaging Berbasis ARIMA</h3>
      </div>

      <p class="subtitle">
        “Untuk membantu perencanaan pakan secara lebih akurat dan efisien”
      </p>
      


      <!-- CTA Button -->
      <div class="cta-button">
        <router-link to="/prediksi" class="start-btn">Mulai Prediksi Sekarang</router-link>
      </div>

      
    </div>

    <!-- ✨ Sekilas Fitur -->
    <section class="features">
      <h3>Fitur Utama Sistem</h3>
      <div class="feature-cards">
        <div class="card">
          <h4>📈 Prediksi Pakan</h4>
          <p>Prediksi kebutuhan pakan ayam berdasarkan data historis menggunakan ARIMA.</p>
        </div>
        <div class="card">
          <h4>📊 Visualisasi Data</h4>
          <p>Tampilan grafik interaktif untuk melihat tren penggunaan pakan.</p>
        </div>
        <div class="card">
          <h4>🕓 Riwayat</h4>
          <p>Menyimpan riwayat prediksi untuk referensi di masa depan.</p>
        </div>
      </div>
    </section>

    <!-- 👣 Langkah Penggunaan -->
    <section class="steps">
      <h3>Cara Menggunakan Sistem</h3>
      <ol>
        <li>Buka halaman <strong>Prediksi</strong>.</li>
        <li>Pilih jumlah periode yang ingin diprediksi.</li>
        <li>Pilih tipe grafik dan klik "Tampilkan Prediksi".</li>
        <li>Lihat hasil prediksi dan simpan jika diperlukan.</li>
      </ol>
    </section>

    <!-- 📞 Footer -->
    <footer class="footer">
      <p>📧 Kontak: feedpredict@example.com | &copy; 2025 FeedPredict</p>
    </footer>
  </main>
</template>

<script setup>
// Tidak ada logic yang diperlukan di sini
</script>

<style scoped>
.main-content {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
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
  margin-top: 1rem;
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

/* CTA Button */
.cta-button {
  margin-top: 1.5rem;
}
.start-btn {
  display: inline-block;
  background-color: #7ca221;
  color: white;
  padding: 10px 20px;
  font-weight: bold;
  border-radius: 8px;
  text-decoration: none;
}
.start-btn:hover {
  background-color: #659117;
}

/* Fitur Section */
.features {
  margin-top: 3rem;
  text-align: center;
}
.features h3 {
  margin-bottom: 1rem;
  font-size: 1.6rem;
}
.feature-cards {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  flex-wrap: wrap;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  max-width: 240px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  background-color: #f9fafb;
}
.card h4 {
  margin-bottom: 0.5rem;
  color: #1f2937;
}
.card p {
  font-size: 0.9rem;
  color: #4b5563;
}

/* Langkah Section */
.steps {
  margin: 3rem auto;
  max-width: 700px;
  text-align: left;
}
.steps h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}
.steps ol {
  padding-left: 1.2rem;
}
.steps li {
  margin-bottom: 0.75rem;
  font-size: 1rem;
}

/* Footer */
.footer {
  text-align: center;
  margin-top: 3rem;
  padding: 1rem;
  font-size: 0.9rem;
  background-color: #f3f4f6;
  color: #4b5563;
}
</style>
