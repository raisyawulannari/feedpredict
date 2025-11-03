<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="title">Login</h2>

      <!-- Google Login Button -->
      <button class="btn-google" @click="loginWithGoogle">
        <img src="@/assets/google-logo.png" alt="Google Logo" class="google-logo" />
        Login with Google
      </button>

      <p class="or-text">atau</p>

      <form class="login-form" @submit.prevent="loginUser">
        <!-- Email -->
        <div class="input-wrapper">
          <input type="email" placeholder="Email" v-model="email" class="input-field" required />
        </div>

        <!-- Password -->
        <div class="input-wrapper">
          <input :type="showPassword ? 'text' : 'password'" placeholder="Password" v-model="password"
            class="input-field" required />
          <i :class="['fa', showPassword ? 'fa-eye-slash' : 'fa-eye']" class="toggle-password"
            @click="togglePassword"></i>
        </div>

        <!-- Options -->
        <div class="options">
          <label>
            <input type="checkbox" v-model="rememberMe" />
            Remember me
          </label>
          <router-link to="/forgot" class="forgot-link">Forgot Password?</router-link>
        </div>

        <!-- Login Button -->
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
      this.errorMessage = "";
      try {
        const res = await axios.post("http://127.0.0.1:8000/api/login", {
          email: this.email,
          password: this.password,
        });

        // simpan token & role
        localStorage.setItem("token", res.data.access_token);
        localStorage.setItem("role", res.data.role);
        localStorage.setItem("name", res.data.name);

        userStore.setUser({
          name: res.data.name,
          role: res.data.role,
          token: res.data.access_token,
        });

        // redirect berdasarkan role
        if (res.data.role === "admin") this.$router.push("/admin/dashboard");
        else this.$router.push("/user/dashboard");
      } catch (err) {
        // tangani error verifikasi
        if (err.response?.status === 403) {
          this.errorMessage = "Akun belum diverifikasi oleh admin";
        } else {
          this.errorMessage = err.response?.data?.detail || "Login gagal";
        }
      }
    },

    loginWithGoogle() {
      if (!window.google) {
        this.errorMessage = "Google API belum siap, reload halaman";
        return;
      }

      const client_id = "YOUR_GOOGLE_CLIENT_ID"; // ganti dengan milikmu
      const googleAuth = window.google.accounts.oauth2.initTokenClient({
        client_id,
        scope: "email profile",
        callback: async (response) => {
          try {
            const res = await axios.post("http://127.0.0.1:8000/api/login-google", {
              id_token: response.access_token,
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
            if (err.response?.status === 403) {
              this.errorMessage = "Akun belum diverifikasi oleh admin";
            } else {
              this.errorMessage = err.response?.data?.detail || "Login Google gagal";
            }
          }
        },
      });

      googleAuth.requestAccessToken();
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
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
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
  color: #b0f2b6;
}

.title {
  font-size: 30px;
  color: #3e8a0b;
  text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.995);
  margin-bottom: 25px;
  font-weight: 600;
}

.btn-google {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #ffffff;
  color: #000;
  padding: 12px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: bold;
  gap: 10px;
  width: 100%;
  margin-bottom: 15px;
  position: relative;
  z-index: 2;
}

.google-logo {
  width: 22px;
  height: 22px;
}

.or-text {
  text-align: center;
  margin: 10px 0 20px;
  color: #b0f2b6;
  font-weight: 500;
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
  color: #065f00;
  transition: box-shadow 0.3s ease;
  box-sizing: border-box;
}

.input-field:focus {
  box-shadow: 0 0 8px rgba(62, 138, 11, 0.7);
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

.options {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #b0f2b6;
  width: 100%;
}

.forgot-link {
  color: #b0f2b6;
  text-decoration: none;
}

.forgot-link:hover {
  color: #065f00;
  text-decoration: underline;
}

.btn-login {
  padding: 14px;
  border-radius: 8px;
  background-color: #3e8a0b;
  color: #ffffff;
  font-weight: bold;
  border: none;
  cursor: pointer;
  font-size: 18px;
  transition: background-color 0.3s ease;
}

.btn-login:hover {
  background-color: #65a832;
  color: #ffffff;
}

.register-text {
  margin-top: 18px;
  font-size: 14px;
  color: #b0f2b6;
}

.register-link {
  color: #3e8a0b;
  font-weight: 500;
  text-decoration: underline;
}

.register-link:hover {
  color: #065f00;
}

.error-message {
  color: #ff7f50;
  margin-top: 12px;
  font-size: 13px;
}
</style>
