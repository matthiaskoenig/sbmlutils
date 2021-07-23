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
        },
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
.overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;

    background-color: rgba(0, 0, 0, 0.5);
    z-index: 2;
}

.overlay-content {
    position: absolute;
    width: 40%;
    height: 40%;
    top: 50%;
    left: 50%;

    transform: translate(-50%, -50%);
    -ms-transform: translate(-50%, -50%);
}

.loader {
    display: flex;
    height: 40%;

    justify-content: center;
    align-items: center;

    background-color: white;
}
</style>
