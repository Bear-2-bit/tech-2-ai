<template>
  <nav class="nav">
    <RouterLink to="/chat">Chat</RouterLink>
    <RouterLink to="/extract">Extract</RouterLink>
    <RouterLink to="/search">Search</RouterLink>
    <RouterLink to="/rag">RAG</RouterLink>
    <RouterLink to="/sql">SQL</RouterLink>
    <RouterLink to="/agent">Agent</RouterLink>
    <RouterLink to="/workflow">Workflow</RouterLink>
    <RouterLink to="/eval">Eval</RouterLink>
    <RouterLink to="/traces">Traces</RouterLink>
  </nav>

  <RouterView />
</template>

<style scoped>
.nav {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid #ddd;
}

.nav a {
  text-decoration: none;
}

.nav a.router-link-active {
  font-weight: bold;
}
</style>
