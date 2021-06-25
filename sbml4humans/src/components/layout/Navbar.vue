<template>
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
        <router-link class="navbar-brand" to="/">
            <img
                class="logo"
                src="https://github.com/matthiaskoenig/sbmlutils/raw/develop/docs_builder/images/sbmlutils-logo-60.png"
            />
            SBML4Humans
        </router-link>

        <!-- Search and Filter component (visible only in report view) -->
        <search-and-filter
            v-if="['Report', 'report'].includes($route.name)"
        ></search-and-filter>

        <!-- Static switch -->
        <div class="static ml-auto" title="Turn ON Static to disconnect from the API">
            <p class="label">Static</p>
            <label class="switch">
                <input
                    ref="static-switch"
                    type="checkbox"
                    v-bind:checked="staticStatus"
                    @change="handleSwitchChange()"
                />
                <span class="slider round"></span>
            </label>
        </div>
    </nav>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

import SearchAndFilter from "@/components/layout/SearchAndFilter.vue";

/**
 * Navbar component for providing main links in the application
 */
export default defineComponent({
    components: {
        "search-and-filter": SearchAndFilter,
    },

    data(): Record<string, unknown> {
        return {
            // stores a copy of the browser's localStorage (not in use currently, FIXME!!)
            staticStatus: window.localStorage.getItem("static") === "true",
        };
    },

    methods: {
        handleSwitchChange(): void {
            const staticSwitch = this.$refs["static-switch"] as HTMLInputElement;
            if (staticSwitch.checked) {
                store.dispatch("updateStatic", true);
                this.staticStatus = window.localStorage.getItem("static") === "true";
            } else {
                store.dispatch("updateStatic", false);
                this.staticStatus = window.localStorage.getItem("static") === "true";
            }
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/Navbar.scss";
</style>
