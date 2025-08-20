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
      showPassword: false
    }
  },
  methods: {
    togglePassword() {
      this.showPassword = !this.showPassword
    },
    async registerUser() {
      try {
        await axios.post('http://127.0.0.1:8000/api/register', {
          name: this.name,
          email: this.email,
          password: this.password
        })
        alert("Registrasi sukses, silakan login")
        this.$router.push('/login')
      } catch (err) {
        this.errorMessage = err.response?.data?.detail || 'Registrasi gagal'
      }
    }
  }
}
</script>

<style scoped>
/* Sama dengan login-container */
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

/* Card transparan dengan efek blur */
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
  color: #f5f5f5;
}

/* Judul register */
.title {
  font-size: 30px;
  color: #ffd369; 
  margin-bottom: 25px;
  font-weight: 600;
}

/* Form input */
.register-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* Input */
.input-field {
  width: 100%;
  padding: 14px 16px;
  border-radius: 8px;
  border: none;
  outline: none;
  font-size: 15px;
  background: rgba(255, 255, 255, 0.85);
  color: #222;
  transition: box-shadow 0.3s ease;
  box-sizing: border-box;
}
.input-field:focus {
  box-shadow: 0 0 8px rgba(255, 211, 105, 0.7);
}

/* Password wrapper */
.password-wrapper {
  position: relative;
  width: 100%;
}
.password-input {
  padding-right: 40px; /* tambahan padding biar sama lebar dgn input lain */
}
.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  color: #555;
  font-size: 16px;
}
.toggle-password:hover {
  color: #fff;
}

/* Button */
.btn-register {
  padding: 14px;
  border-radius: 8px;
  background-color: #763007; /* sama dengan login */
  color: #fff;
  font-weight: bold;
  border: none;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s ease;
}
.btn-register:hover {
  background-color: #ffd369;
  color: #222;
}

/* Teks login */
.login-text {
  margin-top: 18px;
  font-size: 14px;
  color: #f0f0f0;
}
.login-link {
  color: #ffd369;
  font-weight: 500;
  text-decoration: underline;
}
.login-link:hover {
  color: #ffffff;
}

/* Error */
.error-message {
  color: #ff6b6b;
  margin-top: 12px;
  font-size: 13px;
}
</style>
