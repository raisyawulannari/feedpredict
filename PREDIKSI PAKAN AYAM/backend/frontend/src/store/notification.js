// store/notification.js
import { ref } from 'vue'

export const notification = ref({
  show: false,
  message: '',
  type: 'success' // success | error | info
})

export function showNotification(msg, type = 'success') {
  notification.value = { show: true, message: msg, type }
  setTimeout(() => notification.value.show = false, 3000)
}
