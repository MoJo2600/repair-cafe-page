<script setup lang="ts">
import { personName } from '@/utils/person'
import { computed, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useAuthStore } from '@/stores/authStore'
import { useToast } from '@/composables/useToast'

/**
 * Main navigation, by screen size:
 * - lg and up: side menu with labels
 * - md (e.g. tablet landscape): narrow rail, icon above label
 * - smaller: bottom navigation on the main pages; the full menu (admin pages,
 *   profile, logout) opens as an overlay via `open` (app bar menu button)
 */
const open = defineModel<boolean>('open', { default: false })

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()
const { smAndDown, md } = useDisplay()

interface NavItem {
  title: string
  icon: string
  to: string
}

const mainItems: NavItem[] = [
  { title: 'Reparaturen', icon: 'mdi-home', to: '/' },
  { title: 'Reparaturliste', icon: 'mdi-format-list-bulleted', to: '/repairs' },
  { title: 'Kunden', icon: 'mdi-account-group', to: '/customers' },
  { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/dashboard' },
]
const adminItems: NavItem[] = [
  { title: 'Benutzer', icon: 'mdi-account-cog', to: '/users' },
  { title: 'Einstellungen', icon: 'mdi-cog', to: '/settings' },
  { title: 'Styleguide', icon: 'mdi-palette-outline', to: '/styleguide' },
]
// Detail pages (e.g. a repair) have their own back button and bottom action bar;
// the bottom navigation would only take their space
const showBottomNav = computed(
  () => smAndDown.value && mainItems.some((item) => item.to === route.path)
)

const items = computed(() => (authStore.isAdmin ? [...mainItems, ...adminItems] : mainItems))

const currentUserName = computed(() => personName(authStore.currentUser))

// The overlay drawer is only used on small screens; larger ones show a permanent one
const drawerOpen = computed({
  get: () => !smAndDown.value || open.value,
  set: (value: boolean) => {
    open.value = value
  },
})

const loggingOut = shallowRef(false)

async function logout() {
  if (loggingOut.value) return
  loggingOut.value = true
  try {
    await authStore.logout()
    await router.replace({ name: 'Login' })
  } catch {
    toast.error('Abmelden fehlgeschlagen. Bitte erneut versuchen.')
  } finally {
    loggingOut.value = false
  }
}
</script>

<template>
  <v-navigation-drawer
    v-model="drawerOpen"
    :permanent="!smAndDown"
    :temporary="smAndDown"
    :width="md ? 112 : 240"
  >
    <v-list nav>
      <template v-for="item in items" :key="item.to">
        <!-- Rail: icon above label, large touch target -->
        <v-list-item v-if="md" :to="item.to" class="rail-item" min-height="64">
          <div class="d-flex flex-column align-center ga-1 py-1">
            <v-icon :icon="item.icon" />
            <span class="text-label-small text-center">{{ item.title }}</span>
          </div>
        </v-list-item>
        <v-list-item
          v-else
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          min-height="48"
          @click="open = false"
        />
      </template>
    </v-list>

    <template #append>
      <v-divider />
      <v-list v-if="authStore.currentUser" nav aria-label="Benutzerkonto">
        <template v-if="md">
          <v-list-item :to="{ name: 'Profile' }" class="rail-item" min-height="64" aria-label="Mein Profil">
            <div class="d-flex flex-column align-center ga-1 py-1">
              <v-icon icon="mdi-account-circle" />
              <span class="text-label-small text-center">Profil</span>
            </div>
          </v-list-item>
          <v-list-item class="rail-item" min-height="64" :disabled="loggingOut" @click="logout">
            <div class="d-flex flex-column align-center ga-1 py-1">
              <v-icon icon="mdi-logout" />
              <span class="text-label-small text-center">Abmelden</span>
            </div>
          </v-list-item>
        </template>
        <template v-else>
          <v-list-item
            :to="{ name: 'Profile' }"
            prepend-icon="mdi-account-circle"
            :title="currentUserName"
            :subtitle="authStore.currentUser.username"
            aria-label="Mein Profil"
            @click="open = false"
          />
          <v-list-item
            prepend-icon="mdi-logout"
            title="Abmelden"
            :disabled="loggingOut"
            @click="logout"
          />
        </template>
      </v-list>
    </template>
  </v-navigation-drawer>

  <v-bottom-navigation v-if="showBottomNav" grow>
    <v-btn v-for="item in mainItems" :key="item.to" :to="item.to" :value="item.to">
      <v-icon :icon="item.icon" />
      <span>{{ item.title }}</span>
    </v-btn>
  </v-bottom-navigation>
</template>

<style scoped>
.rail-item {
  justify-content: center;
  padding-inline: 4px;
}

/* German labels are long; wrap with hyphenation instead of clipping */
.rail-item .text-label-small {
  hyphens: auto;
  overflow-wrap: anywhere;
  line-height: 1.2;
}
</style>
