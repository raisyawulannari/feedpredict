<template>
  <div>
    <header class="navbar">
      <div class="logo">
        <img src="./assets/FEEDPREDICT.png" alt="Logo Feed Predict" />
      </div>
      <nav class="nav-links">
        <router-link to="/" class="nav-link" exact-active-class="active">Beranda</router-link>
        <router-link to="/prediksi" class="nav-link" exact-active-class="active">Prediksi</router-link>
        <router-link to="/riwayat" class="nav-link" exact-active-class="active">Riwayat</router-link>
      </nav>

      <div class="hallo-btn">
        <button>hallo</button>
      </div>
    </header>

    <router-view />
  </div>
</template>

<script setup>
// tidak perlu logic di sini
</script>

<style scoped>
/* Taruh style navbar yang kamu punya */
.navbar {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  padding-bottom: 1.5rem;
}

.logo img {
  height: 70px;
}

.nav-links {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.nav-link {
  text-decoration: none;
  font-weight: bold;
  color: #5d2d1d;
}

.nav-link.active {
  border-bottom: 2px solid #5d2d1d;
}

.hallo-btn button {
  padding: 10px 10px;
  background-color: #d6d8aa;
  border: none;
  border-radius: 10px;
  font-weight: bold;
  cursor: pointer;
}
</style>
