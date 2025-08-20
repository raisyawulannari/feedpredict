import { reactive, computed } from 'vue'

const userState = reactive({
  name: localStorage.getItem('name') || null,
  role: localStorage.getItem('role') || null,
  token: localStorage.getItem('token') || null
})

const isLoggedIn = computed(() => !!userState.token)
const isAdmin = computed(() => userState.role === 'admin')
const isUser = computed(() => userState.role === 'user')

function setUser(newUser) {
  userState.name = newUser.name
  userState.role = newUser.role
  userState.token = newUser.token

  localStorage.setItem('name', newUser.name)
  localStorage.setItem('role', newUser.role)
  localStorage.setItem('token', newUser.token)
}

function logout() {
  localStorage.removeItem('name')
  localStorage.removeItem('role')
  localStorage.removeItem('token')

  userState.name = null
  userState.role = null
  userState.token = null

  window.location.href = '/login'
}

export default {
  userState,
  isLoggedIn,
  isAdmin,
  isUser,
  setUser,
  logout
}
