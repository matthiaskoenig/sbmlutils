<template>
    <div class="list-group">
        <compartment
            v-for="compt in listOfCompartments"
            v-bind:key="compt.sbo"
            v-bind:info="compt"
        ></compartment>
    </div>
</template>

<script>
import store from "@/store/index";

/* Compartments */
import Compartment from "@/components/sbml/Compartment";

export default {
    components: {
        compartment: Compartment,
    },

    data() {
        return {
            listOfCompartments: [],
        };
    },

    computed: {
        collectCompartments() {
            return store.state.compartments;
        },
    },

    mounted() {
        this.listOfCompartments = this.collectCompartments;
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/listOf/ListOfCompartments.scss";
</style>
