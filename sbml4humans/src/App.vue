<template>
    <navbar class="navbar-fixed" />
    <router-view class="router-view" />
</template>

<script lang="ts">
import Navbar from "@/components/layout/Navbar.vue";

export default {
    name: "app",
    components: {
        Navbar,
    },
};
</script>

<style lang="scss">
@import "@/assets/styles/scss/App.scss";
</style>
