<script setup>
  import { ref } from 'vue';
  import axios from 'axios';

  const message = ref('');

  function fetch_it() {
    fetch('http://127.0.0.1:8000', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        //'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ query: 'Can you tell me what is a dog?' })
    }).then(
      response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      }
    ).then(data => {
        message.value = data['data'];
      }
    );
  }
</script>

<template>
  <div class="sender">
    <button @click="fetch_it">Fetch</button>
    <p>{{ message }}</p>
  </div>
</template>

<style scoped>
.sender {
  background-color: #66CCFF;
}
</style>
