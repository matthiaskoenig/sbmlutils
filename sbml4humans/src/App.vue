<template>
    <navbar />
    <main-window />
</template>

<script lang="ts">
import Navbar from '@/components/Navbar.vue';
import MainWindow from '@/components/MainWindow.vue';

export default {
    name: 'app',
    components: {
        'navbar': Navbar,
        'main-window': MainWindow,
    },
};
</script>
