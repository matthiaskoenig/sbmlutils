<template>
    <div class="search">
        <input
            class="form-control"
            type="text"
            placeholder="&nbsp; &#128270; &nbsp; Search for an SBML Component"
            @input="updateSearchQuery"
        />
    </div>
</template>

<script>
import store from "@/store/index";

export default {
    methods: {
        updateSearchQuery(e) {
            store.dispatch("updateSearchQuery", e.target.value);
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/Search.scss";
</style>
