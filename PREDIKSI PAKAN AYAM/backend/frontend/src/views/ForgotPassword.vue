<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="title">Reset Password</h2>

      <form class="login-form" @submit.prevent="resetPassword">
        <!-- Email -->
        <div class="input-wrapper">
          <input
            type="email"
            placeholder="Email"
            v-model="email"
            class="input-field"
            required
          />
        </div>

        <!-- Password Baru -->
        <div class="input-wrapper">
          <input
            :type="showPassword ? 'text' : 'password'"
            placeholder="Password Baru"
            v-model="password"
            class="input-field"
            required
          />
          <i
            :class="['fa', showPassword ? 'fa-eye-slash' : 'fa-eye']"
            class="toggle-password"
            @click="togglePassword"
          ></i>
        </div>

        <!-- Konfirmasi Password -->
        <div class="input-wrapper">
          <input
            :type="showConfirmPassword ? 'text' : 'password'"
            placeholder="Konfirmasi Password Baru"
            v-model="confirmPassword"
            class="input-field"
            required
          />
          <i
            :class="['fa', showConfirmPassword ? 'fa-eye-slash' : 'fa-eye']"
            class="toggle-password"
            @click="toggleConfirmPassword"
          ></i>
        </div>

        <!-- Button -->
        <button type="submit" class="btn-login">Reset Password</button>
      </form>

      <!-- Error -->
      <p class="error-message" v-if="errorMessage">{{ errorMessage }}</p>

      <!-- Back to Login -->
      <p class="register-text">
        Sudah ingat password?
        <router-link to="/login" class="register-link">Login</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      email: "",
      password: "",
      confirmPassword: "",
      errorMessage: "",
      showPassword: false,
      showConfirmPassword: false,
    };
  },
  methods: {
    togglePassword() {
      this.showPassword = !this.showPassword;
    },
    toggleConfirmPassword() {
      this.showConfirmPassword = !this.showConfirmPassword;
    },
    async resetPassword() {
      if (this.password !== this.confirmPassword) {
        this.errorMessage = "Password baru dan konfirmasi tidak sama!";
        return;
      }

      try {
        await axios.post("http://127.0.0.1:8000/api/reset-password", {
          email: this.email,
          new_password: this.password,
        });

        alert("Password berhasil direset! Silakan login kembali.");
        this.$router.push("/login");
      } catch (err) {
        this.errorMessage =
          err.response?.data?.detail || "Gagal reset password";
      }
    },
  },
};
</script>

<style scoped>
.login-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: url("@/assets/home-ayam.jpg") no-repeat center center/cover;
  font-family: "Poppins", sans-serif;
}

.login-container::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.45);
}

.login-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  padding: 40px 30px;
  border-radius: 14px;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.4);
  width: 360px;
  text-align: center;
  color: #b0f2b6; /* hijau lembut */
}

.title {
  font-size: 28px;
  color: #3e8a0b; /* hijau utama */
 text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.995);  margin-bottom: 20px;
  font-weight: 600;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  width: 100%;
}

.input-wrapper {
  position: relative;
  width: 100%;
}

.input-field {
  width: 100%;
  padding: 14px 40px 14px 14px;
  border-radius: 8px;
  border: none;
  outline: none;
  font-size: 15px;
  background: rgba(255, 255, 255, 0.85);
  color: #065f00; /* teks hijau gelap */
  transition: box-shadow 0.3s ease;
  box-sizing: border-box;
}
.input-field:focus {
  box-shadow: 0 0 8px rgba(62, 138, 11, 0.7); /* highlight hijau */
}

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  color: #065f00; /* hijau gelap */
  font-size: 16px;
}
.toggle-password:hover {
  color: #3e8a0b; /* hijau utama */
}

.btn-login {
  padding: 14px;
  border-radius: 8px;
  background-color: #3e8a0b; /* hijau utama */
  color: #ffffff; /* teks putih */
  font-weight: bold;
  border: none;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s ease;
}
.btn-login:hover {
  background-color: #65a832; /* hijau terang */
  color: #ffffff;
}

.register-text {
  margin-top: 18px;
  font-size: 14px;
  color: #b0f2b6; /* hijau lembut */
}
.register-link {
  color: #3e8a0b; /* hijau utama */
  font-weight: 500;
  text-decoration: underline;
}
.register-link:hover {
  color: #065f00; /* hijau gelap */
}

.error-message {
  color: #065f00; /* hijau gelap */
  margin-top: 12px;
  font-size: 13px;
}
</style>
