<template>
  <v-app>
    <v-app-bar elevation="1">
      <div class="d-flex align-center flex-grow-1">
        <v-img src="/icon.ico" alt="Logo" contain max-width="60" max-height="60" class="mr-3 ml-2" />
        <span style="color: #B63400; font-size: 2rem; font-weight: 300; white-space: nowrap;">
          MEQUATLING
        </span>
      </div>
      <v-spacer />
      <v-btn :to="'/dashboard'" component="RouterLink">Dashboard</v-btn>
      <v-btn :to="'/animals'" component="RouterLink">Animals</v-btn>
      <v-btn :to="'/camps'" component="RouterLink">Camps</v-btn>
      <v-btn :to="'/groups'" component="RouterLink">Groups</v-btn>
      <v-btn :to="'/stocks'" component="RouterLink">Stocks</v-btn>
      <v-btn :to="'/vaccinations-history'" component="RouterLink">Vaccinations</v-btn>
    </v-app-bar>
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>