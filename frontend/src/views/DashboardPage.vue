<script setup lang="ts">
import DashboardSummary from '@/components/dashboard/DashboardSummary.vue'
import PageHeader from '@/components/ui/PageHeader.vue'

/** Repair figures for helpers; the lock screen shows the same summary. */
</script>

<template>
  <v-container fluid class="dashboard">
    <PageHeader title="Dashboard" subtitle="Diese Übersicht erscheint auch auf dem Sperrbildschirm" />
    <DashboardSummary />
  </v-container>
</template>

<style scoped>
.dashboard {
  max-width: 1600px;
}
</style>
