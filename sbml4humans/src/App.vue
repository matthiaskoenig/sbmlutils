<template>
    <navbar />
    <main-window />
</template>

<script lang="ts">
import Navbar from "@/components/layout/Navbar.vue";
import MainWindow from "@/components/layout/MainWindow.vue";

import mixin from "@/mixin";

export default {
    name: "app",
    components: {
        navbar: Navbar,
        "main-window": MainWindow,
    },
    mixins: [mixin],
};
</script>

<style lang="scss">
@import "@/assets/styles/scss/App.scss";
</style>
