<template>
    <router-view class="main-view" />
</template>

<script lang="ts">
import { defineComponent } from "@vue/runtime-core";

/*
 * Master component which holds all the views.
 */
export default defineComponent({});
</script>

<style lang="scss" scoped>
.main-view {
    padding-bottom: 20px;
}
</style>
