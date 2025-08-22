<template>
  <div class="kelola-user-container">
    <h1 class="title">Kelola User</h1>

    <div class="table-wrapper">
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
              <select v-model="userItem.role" class="role-select">
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
            </td>
            <td>
              <button @click="updateRole(userItem)" class="btn-save">Simpan</button>
              <button @click="deleteUser(userItem)" class="btn-delete">Hapus</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

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
const token = userStore.userState?.token || ''

// Ambil semua user
const fetchUsers = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/admin/users', {
      headers: { Authorization: `Bearer ${token}` }
    })
    // Perhatikan di sini: res.data.users
    users.value = res.data.users || []
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

// Hapus user
const deleteUser = async (userItem) => {
  successMessage.value = ''
  errorMessage.value = ''
  if (!confirm(`Apakah Anda yakin ingin menghapus user ${userItem.name}?`)) return

  try {
    await axios.delete(`http://127.0.0.1:8000/api/admin/users/${userItem.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    successMessage.value = `User ${userItem.name} berhasil dihapus`
    users.value = users.value.filter(u => u.id !== userItem.id)
  } catch (err) {
    console.error(err)
    errorMessage.value = `Gagal menghapus user ${userItem.name}`
  }
}

onMounted(fetchUsers)
</script>

<style scoped>
.kelola-user-container {
  padding: 2rem;
  background: #f0faf0;
  min-height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  color: #1b4d1b;
  text-align: center;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

.table-wrapper {
  overflow-x: auto;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  background: #ffffff;
  box-shadow: 0 4px 15px rgba(0,0,0,0.08);
  border-radius: 10px;
  overflow: hidden;
}

.user-table th, .user-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #e6f0e6;
  font-size: 14px;
}

.user-table th {
  background: #c8e6c9;
  color: #1b4d1b;
  font-weight: 600;
}

.user-table tr:hover {
  background: #eaf6ea;
  transition: background 0.2s;
}

.role-select {
  padding: 6px 8px;
  border-radius: 5px;
  border: 1px solid #a3d9a3;
  background: #f8fff8;
  transition: all 0.2s;
}

.role-select:focus {
  border-color: #1b4d1b;
  box-shadow: 0 0 5px rgba(27,77,27,0.3);
  outline: none;
}

.btn-save {
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  background: linear-gradient(45deg, #4caf50, #2e7d32);
  color: white;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
  margin-right: 5px;
}

.btn-save:hover {
  background: linear-gradient(45deg, #2e7d32, #1b4d1b);
}

.btn-delete {
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  background-color: #d9534f;
  color: white;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-delete:hover {
  background-color: #c9302c;
}

.success-message {
  color: #2e7d32;
  font-weight: 600;
  margin-top: 1rem;
  text-align: center;
}

.error-message {
  color: #c62828;
  font-weight: 600;
  margin-top: 1rem;
  text-align: center;
}

@media (max-width: 768px) {
  .user-table th, .user-table td {
    padding: 10px 12px;
    font-size: 13px;
  }

  .btn-save, .btn-delete {
    padding: 5px 10px;
    font-size: 13px;
  }
}
</style>
