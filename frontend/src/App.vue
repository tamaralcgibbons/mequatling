<template>
  <v-app>
    <v-app-bar color="white" :height="96" elevation="2">
        <v-container class="d-flex align-center">
            <v-img src="/icon.ico" alt="Mequatling" max-height="56" max-width="56" class="mr-3" cover />
            <v-app-bar-title class="text-h5" style="color:#B63400">MEQUATLING</v-app-bar-title>
            <v-spacer />
            <v-btn variant="text" color="primary" :to="{ name: 'dashboard' }">Dashboard</v-btn>
            <v-btn variant="text" color="primary" :to="{ name: 'animals' }">Animals</v-btn>
            <v-btn variant="text" color="primary" :to="{ name: 'camps' }">Camps</v-btn>
            <v-btn variant="text" color="primary" :to="{ name: 'stocks' }">Stocks</v-btn>
        </v-container>
    </v-app-bar>

    <v-main class="bg-white">
      <RouterView />
    </v-main>
  </v-app>
</template>