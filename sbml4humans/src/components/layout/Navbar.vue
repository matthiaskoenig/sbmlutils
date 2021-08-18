<template>
    <menubar :model="items">
        <template #start>
            <div style="display: flex">
            <img alt="logo" src="../../../public/sbmlutils-logo-60.png" height="40" class="p-mr-2">
            <h2 class="">SBML4Humans</h2>
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
.logo {
    height: 40px;
    margin-right: 10px;
    display: inline-flex;
}

.sbmlhumans {
    text-decoration: none;
    color: black;
    text-decoration-line: none;
}

.static {
    height: inherit;
    display: flex;
    flex-direction: row;
}

.label {
    color: black;
    margin-right: 7px;
    height: max-content;
    margin-top: auto;
    margin-bottom: auto;
}

/* Toggle Switch */
.switch {
    position: relative;
    display: inline-block;
    width: 40px;
    height: 20px;
    margin-top: auto;
    margin-bottom: auto;
}

/* Hide default HTML checkbox */
.switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

/* The slider */
.slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    -webkit-transition: 0.4s;
    transition: 0.4s;
}

.slider:before {
    position: absolute;
    content: "";
    height: 20px;
    width: 20px;
    left: 0px;
    bottom: 0px;
    background-color: white;
    -webkit-transition: 0.4s;
    transition: 0.4s;
}

input:checked + .slider {
    background-color: #2196f3;
}

input:focus + .slider {
    box-shadow: 0 0 1px #2196f3;
}

input:checked + .slider:before {
    -webkit-transform: translateX(26px);
    -ms-transform: translateX(26px);
    transform: translateX(26px);
}

/* Rounded sliders */
.slider.round {
    border-radius: 20px;
}

.slider.round:before {
    border-radius: 50%;
}
</style>
