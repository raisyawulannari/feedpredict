<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="title">Login</h2>

      <form class="login-form" @submit.prevent="loginUser">
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

        <!-- Password -->
        <div class="input-wrapper">
          <input
            :type="showPassword ? 'text' : 'password'"
            placeholder="Password"
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

        <!-- Options -->
        <div class="options">
          <label>
            <input type="checkbox" v-model="rememberMe" />
            Remember me
          </label>
          <router-link to="/forgot" class="forgot-link">Forgot Password?</router-link>
        </div>

        <!-- Button -->
        <button type="submit" class="btn-login">Login</button>
      </form>

      <!-- Error -->
      <p class="error-message" v-if="errorMessage">{{ errorMessage }}</p>

      <!-- Register -->
      <p class="register-text">
        Don't have an account?
        <router-link to="/register" class="register-link">Register</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import userStore from "@/store/user.js";

export default {
  data() {
    return {
      email: "",
      password: "",
      rememberMe: false,
      errorMessage: "",
      showPassword: false,
    };
  },
  mounted() {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");
    if (token && role) {
      if (role === "admin") this.$router.push("/admin/dashboard");
      else this.$router.push("/user/dashboard");
    }
  },
  methods: {
    togglePassword() {
      this.showPassword = !this.showPassword;
    },
    async loginUser() {
      try {
        const res = await axios.post("http://127.0.0.1:8000/api/login", {
          email: this.email,
          password: this.password,
        });

        localStorage.setItem("token", res.data.access_token);
        localStorage.setItem("role", res.data.role);
        localStorage.setItem("name", res.data.name);

        userStore.setUser({
          name: res.data.name,
          role: res.data.role,
          token: res.data.access_token,
        });

        if (res.data.role === "admin") this.$router.push("/admin/dashboard");
        else this.$router.push("/user/dashboard");
      } catch (err) {
        this.errorMessage = err.response?.data?.detail || "Login gagal";
      }
    },
  },
};
</script>

<style scoped>
/* Container dengan background peternakan ayam */
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
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
}

/* Card transparan dengan efek blur */
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
  color: #f5f5f5;
}

/* Judul login */
.title {
  font-size: 30px;
  color: #ffd369;
  margin-bottom: 25px;
  font-weight: 600;
}

/* Form */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  width: 100%; /* form full mengikuti card */
}

/* Wrapper supaya input & password sama lebar */
.input-wrapper {
  position: relative;
  width: 100%;
}

/* Input field */
.input-field {
  width: 100%;
  padding: 14px 40px 14px 14px; /* space kanan buat icon mata */
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

/* Password toggle icon */
.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  color: #555;
  font-size: 16px;
}

/* Options */
.options {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #f0f0f0;
  width: 100%;
}

.forgot-link {
  color: #ffd369;
  text-decoration: none;
}
.forgot-link:hover {
  text-decoration: underline;
}

/* Button */
.btn-login {
  padding: 14px;
  border-radius: 8px;
  background-color: #763007;
  color: #fff;
  font-weight: bold;
  border: none;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s ease;
}
.btn-login:hover {
  background-color: #ffd369;
  color: #222;
}

/* Register link */
.register-text {
  margin-top: 18px;
  font-size: 14px;
  color: #f0f0f0;
}
.register-link {
  color: #ffd369;
  font-weight: 500;
  text-decoration: underline;
}
.register-link:hover {
  color: #ffffff;
}

/* Error */
.error-message {
  color: #ff6b6b;
  margin-top: 12px;
  font-size: 13px;
}
</style>
