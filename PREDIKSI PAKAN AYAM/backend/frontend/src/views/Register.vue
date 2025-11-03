<template>
  <div class="register-container">
    <div class="register-card">
      <h2 class="title">Register</h2>

      <form @submit.prevent="registerUser" class="register-form">
        <input 
          v-model="name" 
          type="text"
          placeholder="Nama Lengkap" 
          required 
          class="input-field"
        />

        <input 
          v-model="email" 
          type="email"
          placeholder="Email" 
          required
          class="input-field"
        />

        <!-- Password dengan toggle 👁️ -->
        <div class="password-wrapper">
          <input
            :type="showPassword ? 'text' : 'password'"
            v-model="password"
            placeholder="Password"
            required
            class="input-field password-input"
          />
          <span class="toggle-password" @click="togglePassword">
            <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
          </span>
        </div>

        <button type="submit" class="btn-register">Register</button>
      </form>

      <p class="error-message" v-if="errorMessage">{{ errorMessage }}</p>

      <p class="info-message" v-if="infoMessage">{{ infoMessage }}</p>

      <p class="login-text">
        Sudah punya akun? 
        <router-link to="/login" class="login-link">Login</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  data() {
    return {
      name: '',
      email: '',
      password: '',
      errorMessage: '',
      infoMessage: '',
      showPassword: false
    }
  },
  methods: {
    togglePassword() {
      this.showPassword = !this.showPassword
    },
    async registerUser() {
      this.errorMessage = ''
      this.infoMessage = ''
      try {
        await axios.post('http://127.0.0.1:8000/api/register', {
          name: this.name,
          email: this.email,
          password: this.password
        })
        // Inform user bahwa harus diverifikasi admin
        this.infoMessage = "Registrasi sukses! Akun Anda akan diverifikasi oleh admin sebelum bisa login."
        // Reset form
        this.name = ''
        this.email = ''
        this.password = ''
      } catch (err) {
        this.errorMessage = err.response?.data?.detail || 'Registrasi gagal'
      }
    }
  }
}
</script>

<style scoped>
.register-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: url("@/assets/home-ayam.jpg") no-repeat center center/cover;
  font-family: 'Poppins', sans-serif;
}

.register-container::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.45);
}

.register-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  padding: 40px 30px;
  border-radius: 14px;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.4);
  width: 360px;
  text-align: center;
  color: #b0f2b6;
}

.title {
  font-size: 30px;
  color: #3e8a0b;
  text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.995);
  margin-bottom: 25px;
  font-weight: 600;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.input-field {
  width: 100%;
  padding: 14px 16px;
  border-radius: 8px;
  border: none;
  outline: none;
  font-size: 15px;
  background: rgba(255, 255, 255, 0.85);
  color: #065f00;
  transition: box-shadow 0.3s ease;
  box-sizing: border-box;
}
.input-field:focus {
  box-shadow: 0 0 8px rgba(62, 138, 11, 0.7);
}

.password-wrapper {
  position: relative;
  width: 100%;
}
.password-input {
  padding-right: 40px;
}
.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  color: #065f00;
  font-size: 16px;
}
.toggle-password:hover {
  color: #3e8a0b;
}

.btn-register {
  padding: 14px;
  border-radius: 8px;
  background-color: #3e8a0b;
  color: #ffffff;
  font-weight: bold;
  border: none;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s ease;
}
.btn-register:hover {
  background-color: #65a832;
  color: #ffffff;
}

.login-text {
  margin-top: 18px;
  font-size: 14px;
  color: #b0f2b6;
}
.login-link {
  color: #3e8a0b;
  font-weight: 500;
  text-decoration: underline;
}
.login-link:hover {
  color: #065f00;
}

.error-message {
  color: #ff7f50;
  margin-top: 12px;
  font-size: 13px;
}

.info-message {
  color: #b0f2b6;
  margin-top: 12px;
  font-size: 13px;
  font-style: italic;
}
</style>
