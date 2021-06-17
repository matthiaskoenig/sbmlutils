<template>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <img
            class="logo"
            src="https://github.com/matthiaskoenig/sbmlutils/raw/develop/docs_builder/images/sbmlutils-logo-60.png"
        />
        <router-link class="navbar-brand" to="/"> SBML4Humans </router-link>

        <button
            class="navbar-toggler"
            type="button"
            data-toggle="collapse"
            data-target="#navbarSupportedContent"
            aria-controls="navbarSupportedContent"
            aria-expanded="false"
            aria-label="Toggle navigation"
        >
            <span class="navbar-toggler-icon"></span>
        </button>

        <!-- Static switch -->

        <div class="collapse navbar-collapse" id="navbarSupportedContent">
            <ul class="navbar-nav ml-auto mr-20">
                <li class="nav-item">
                    <div
                        class="nav-link d-flex"
                        title="Turn ON Static to disconnect from the API"
                    >
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
                </li>
            </ul>
        </div>
    </nav>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

/**
 * Navbar component for providing main links in the application
 */
export default defineComponent({
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
