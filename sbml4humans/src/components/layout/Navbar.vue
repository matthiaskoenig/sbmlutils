<template>
    <menubar :model="items">
        <template #start>
            <div class="p-d-flex">
                <router-link to="/">
                    <img
                        to="/"
                        alt="logo"
                        src="@/assets/images/sbml4humans-192x192.png"
                        height="35"
                    />
                </router-link>
                <router-link to="/">
                    <span class="sbml4humans p-mx-3" style="color: black"
                        >SBML4Humans</span
                    >
                </router-link>
            </div>
        </template>
    </menubar>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import store from "@/store";

/**
 * Navbar component for providing main links in the application
 */
export default defineComponent({
    data() {
        return {
            items: [
                {
                    label: "Home",
                    icon: "pi pi-fw pi-home",
                    to: "/",
                },
                {
                    label: "Examples",
                    icon: "pi pi-fw pi-list",
                    to: "/examples",
                },
                {
                    label: "About",
                    icon: "pi pi-fw pi-info-circle",
                    to: "/about",
                },

                {
                    label: "Report issue",
                    icon: "pi pi-fw pi-pencil",
                    url: "https://github.com/matthiaskoenig/sbmlutils/issues/new/choose",
                },
                {
                    label: "Source",
                    icon: "pi pi-fw pi-github",
                    url: "https://github.com/matthiaskoenig/sbmlutils",
                },
            ],
        };
    },
});
</script>

<style lang="scss" scoped>
.sbml4humans {
    font-family: "Roboto Slab", serif;
    font-size: 30px;
}
</style>
