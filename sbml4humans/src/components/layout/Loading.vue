<template>
    <div v-if="loading" class="overlay">
        <div class="overlay-content">
            <div class="loader">
                <div>
                    <a-spin class="px-3" size="large" />
                    <strong>{{ loadingMsg }}</strong>
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

export default defineComponent({
    props: {
        parent: {
            type: String,
        },
        msg: {
            type: String,
        }
    },

    computed: {
        loading(): boolean {
            let key: string = this.parent + "Loading"; // key is either "exampleLoading" or "fileLoading"

            return store.state[key];
        },

        loadingMsg(): string {
            return store.state.loadingMessage;
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/Loading.scss";
</style>
