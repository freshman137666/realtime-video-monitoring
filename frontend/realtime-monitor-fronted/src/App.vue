<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header>
    <div class="wrapper">
      <nav>
        <RouterLink to="/">监控系统</RouterLink>
        <RouterLink to="/about">关于</RouterLink>
      </nav>
    </div>
  </header>

  <RouterView />
</template>

<style>
@import './assets/base.css';

#app {
  max-width: 100%;
  margin: 0 auto;
  padding: 0;
  font-weight: normal;
}

header {
  background-color: #2c3e50;
  padding: 10px 0;
}

.wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
}

nav {
  display: flex;
  gap: 20px;
}

nav a {
  padding: 10px 15px;
  color: white;
  text-decoration: none;
  font-weight: bold;
  border-radius: 4px;
}

nav a:hover {
  background-color: #1e2a36;
}

nav a.router-link-exact-active {
  background-color: #42b983;
}

@media (min-width: 1024px) {
  body {
    display: flex;
    place-items: center;
  }
}
</style>
