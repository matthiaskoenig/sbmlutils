<template>
    <menubar :model="items">
        <template #start>
            <div style="display: flex">
                <img
                    alt="logo"
                    src="../../../public/sbmlutils-logo-60.png"
                    height="40"
                    width="100"
                    class="p-mr-2 p-mt-3"
                />
                <h2 class="brand">SBML4Humans</h2>
            </div>
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
.p-menubar {
    background-color: white;
    border: none;
    padding: 0 20px;
}

.logo {
    height: 40px;
    margin-right: 10px;
    display: inline-flex;
}

.brand {
    text-decoration: none;
    color: rgb(54, 53, 53);
    text-decoration-line: none;
    font-weight: 500;
}
</style>
