<template>
    <navbar />
    <main-window />
</template>

<script lang="ts">
import Navbar from '@/components/layout/Navbar.vue';
import MainWindow from '@/components/layout/MainWindow.vue';

export default {
    name: 'app',
    components: {
        'navbar': Navbar,
        'main-window': MainWindow,
    },
};
</script>
