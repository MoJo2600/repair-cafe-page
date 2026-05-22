<template>
  <v-container>
    <v-card>
      <v-card-title>API Integration Example</v-card-title>
      <v-card-text>
        <v-alert v-if="error" type="error" class="mb-4">
          {{ error }}
        </v-alert>

        <v-btn 
          color="primary" 
          @click="fetchData" 
          :loading="loading"
          class="mb-4"
        >
          Fetch Data from Flask API
        </v-btn>

        <v-card v-if="data" variant="outlined">
          <v-card-text>
            <pre>{{ JSON.stringify(data, null, 2) }}</pre>
          </v-card-text>
        </v-card>

        <v-divider class="my-6"></v-divider>

        <h3 class="text-h6 mb-3">Send Data to API</h3>
        <v-text-field
          v-model="inputData"
          label="Enter some data"
          hint="This will be sent to the Flask API"
        ></v-text-field>

        <v-btn 
          color="secondary" 
          @click="postData"
          :loading="posting"
          :disabled="!inputData"
          class="mt-2"
        >
          Send to API
        </v-btn>

        <v-alert v-if="postResponse" type="success" class="mt-4">
          Response: {{ postResponse }}
        </v-alert>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Types
interface ApiResponse {
  message: string
  data?: any
}

// State
const data = ref<ApiResponse | null>(null)
const error = ref<string>('')
const loading = ref(false)
const inputData = ref('')
const posting = ref(false)
const postResponse = ref<string>('')

// Functions
const fetchData = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await fetch('/api/your-endpoint')
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const result = await response.json()
    data.value = result
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'An error occurred'
    console.error('Fetch error:', e)
  } finally {
    loading.value = false
  }
}

const postData = async () => {
  posting.value = true
  postResponse.value = ''
  
  try {
    const response = await fetch('/api/your-endpoint', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ data: inputData.value })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const result = await response.json()
    postResponse.value = result.message || 'Success!'
    inputData.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'An error occurred'
    console.error('Post error:', e)
  } finally {
    posting.value = false
  }
}
</script>
