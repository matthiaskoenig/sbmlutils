<template>
    <h5>List of SBases</h5>
    <list-of-sbases></list-of-sbases>
    <br />
    <h5>List of Compartments</h5>
    <list-of-compartments></list-of-compartments>
</template>

<script>
/* Compartments */
import ListOfSBases from "@/components/sbml/listOf/ListOfSBases";
import ListOfCompartments from "@/components/sbml/listOf/ListOfCompartments";

export default {
    components: {
        "list-of-sbases": ListOfSBases,
        "list-of-compartments": ListOfCompartments,
    },
};
</script>
