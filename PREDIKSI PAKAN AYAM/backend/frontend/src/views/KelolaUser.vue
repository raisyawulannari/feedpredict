<template>
  <div class="kelola-user-container">
    <h1 class="title">Kelola User</h1>

    <table class="user-table">
      <thead>
        <tr>
          <th>No</th>
          <th>Nama</th>
          <th>Email</th>
          <th>Role</th>
          <th>Aksi</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(userItem, index) in users" :key="userItem.id">
          <td>{{ index + 1 }}</td>
          <td>{{ userItem.name }}</td>
          <td>{{ userItem.email }}</td>
          <td>
            <select v-model="userItem.role">
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </td>
          <td>
            <button @click="updateRole(userItem)" class="btn-save">Simpan</button>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-if="successMessage" class="success-message">{{ successMessage }}</p>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import userStore from '@/store/user.js'

const users = ref([])
const successMessage = ref('')
const errorMessage = ref('')
const token = userStore.userState?.token || ''  // jaga-jaga kalau token null

// Ambil daftar user dari backend
const fetchUsers = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/admin/users', {
      headers: { Authorization: `Bearer ${token}` }
    })
    users.value = res.data
  } catch (err) {
    console.error(err)
    errorMessage.value = 'Gagal mengambil data user'
  }
}

// Update role user
const updateRole = async (userItem) => {
  successMessage.value = ''
  errorMessage.value = ''
  try {
    await axios.put(`http://127.0.0.1:8000/api/admin/users/${userItem.id}`, 
      { role: userItem.role },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    successMessage.value = `Role ${userItem.name} berhasil diperbarui`
  } catch (err) {
    console.error(err)
    errorMessage.value = `Gagal memperbarui role ${userItem.name}`
  }
}

onMounted(fetchUsers)
</script>


<style scoped>
.kelola-user-container {
  padding: 2rem;
  background: #fefaf5;
  min-height: 100vh;
}

.title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: #5d2d1d;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
  border-radius: 8px;
  overflow: hidden;
}

.user-table th, .user-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.user-table th {
  background: #f3d1b0;
  color: #3e1f0f;
}

.user-table tr:hover {
  background: #fdf2e9;
}

select {
  padding: 5px;
  border-radius: 5px;
  border: 1px solid #ccc;
}

.btn-save {
  padding: 5px 12px;
  border: none;
  border-radius: 5px;
  background-color: #5d2d1d;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-save:hover {
  background-color: #a35d2d;
}

.success-message { color: green; margin-top: 1rem; }
.error-message { color: red; margin-top: 1rem; }
</style>
