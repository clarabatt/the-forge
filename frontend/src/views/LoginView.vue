<script setup lang="ts">
function loginWithGoogle() {
  window.location.href = '/auth/google/login'
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-title">The Forge</h1>
      <p class="login-subtitle">AI-powered résumé tailoring</p>
      <button class="btn-google" @click="loginWithGoogle">
        Sign in with Google
      </button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-bg-subtle);
}

.login-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 48px 40px;
  text-align: center;
  width: 100%;
  max-width: 380px;
}

.login-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
}

.login-subtitle {
  color: var(--color-text-muted);
  margin-bottom: 32px;
}

.btn-google {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;

  &:hover {
    background: var(--color-primary-hover);
  }
}
</style>
