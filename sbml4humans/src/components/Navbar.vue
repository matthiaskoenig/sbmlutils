<template>
    <nav class="navbar navbar-dark bg-dark">
        <router-link class="navbar-brand" to="/">SBML4Humans</router-link>

        <!-- Static switch -->
        <div class="static d-flex ml-auto mt-auto mb-auto">
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

        <div class="collapse navbar-collapse" id="navbarSupportedContent">
            <ul class="navbar-nav ml-auto">
                <li class="nav-item active">
                    <router-link class="nav-link" to="/">Home</router-link>
                </li>
                <li class="nav-item active" v-if="!staticStatus">
                    <router-link class="nav-link" to="/examples">Examples</router-link>
                </li>
                <li class="nav-item active" v-if="!staticStatus">
                    <router-link class="nav-link" to="/uploadSBML"
                        >Upload SBML</router-link
                    >
                </li>
            </ul>
        </div>
    </nav>
</template>

<script>
import store from "@/store/index";

export default {
    data() {
        return {
            // stores a copy of the browser's localStorage (not in use currently, FIXME!!)
            storage: {},
        };
    },

    methods: {
        handleSwitchChange() {
            const staticSwitch = this.$refs["static-switch"];
            console.log("static switch");
            if (staticSwitch.checked) {
                store.dispatch("updateStatic", true);
            } else {
                store.dispatch("updateStatic", false);
            }
        },
    },

    computed: {
        staticStatus() {
            return store.state.static;
        },
    },

    watch: {
        staticStatus() {
            /* storage gets updated only when the Static flag is changed in the Vuex state
                (which is also reflected in the localStorage) */
            this.storage = localStorage;
        },
    },
};
</script>

<style lang="scss" scoped>
@import "../assets/styles/scss/components/Navbar.scss";
</style>
