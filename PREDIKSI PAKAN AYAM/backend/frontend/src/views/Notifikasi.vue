<template>
  <div class="notification-container">
    <h2 class="title">Notifikasi Sistem</h2>
    <ul>
      <li v-for="(notif, index) in notifications" :key="index" :class="notif.type">
        <span class="icon">⚠️</span> {{ notif.message }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const notifications = ref([])

onMounted(async () => {
  try {
    const res = await fetch('http://localhost:8000/get_notifications')
    const data = await res.json()
    notifications.value = data.notifications
  } catch (error) {
    notifications.value = [{ message: 'Gagal memuat notifikasi.', type: 'error' }]
  }
})
</script>

<style scoped>
.notification-container {
  padding: 1rem;
  background-color: #fefae0;
  border: 1px solid #ccc;
  border-radius: 8px;
}

.title {
  margin-bottom: 1rem;
  font-weight: bold;
}

li {
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  border-left: 4px solid orange;
}

li.critical {
  border-left-color: red;
  background-color: #ffe5e5;
}

li.warning {
  border-left-color: orange;
  background-color: #fff5e0;
}

.icon {
  margin-right: 0.5rem;
}
</style>
