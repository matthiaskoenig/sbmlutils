<template>
    <menubar :model="items">
        <template #start>
            <img alt="logo" src="../../../public/sbmlutils-logo-60.png" height="40" class="p-mr-2">
            <span class="title">SBML4Humans</span>
        </template>
    </menubar>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

/**
 * Navbar component for providing main links in the application
 */
export default defineComponent({

    // FIXME: handle static content
    // data(): Record<string, unknown> {
    //     return {
    //         // stores a copy of the browser's localStorage (not in use currently, FIXME!!)
    //         staticStatus: window.localStorage.getItem("static") === "true",
    //     };
    // },
    //
    // methods: {
    //     handleSwitchChange(): void {
    //         const staticSwitch = this.$refs["static-switch"] as HTMLInputElement;
    //         if (staticSwitch.checked) {
    //             store.dispatch("updateStatic", true);
    //             this.staticStatus = window.localStorage.getItem("static") === "true";
    //         } else {
    //             store.dispatch("updateStatic", false);
    //             this.staticStatus = window.localStorage.getItem("static") === "true";
    //         }
    //     },
    // },
});
</script>

<style lang="scss" scoped>
.title {
    font-weight: bold;
    font-size: x-large;
}
</style>
