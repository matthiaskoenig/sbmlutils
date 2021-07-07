<template>
    <a-tabs default-active-key="1">
        <a-tab-pane key="1" tab="List View">
            <div class="tab-container">
                <list-of-sbases></list-of-sbases>
            </div>
        </a-tab-pane>
        <a-tab-pane key="2" tab="Table View">
            <div class="tab-container">
                <list-of-tables></list-of-tables>
            </div>
        </a-tab-pane>
    </a-tabs>
</template>

<script lang="ts">
import ListOfSBases from "@/components/sbmlmisc/ListOfSBases.vue";
import ListOfTables from "@/components/sbmlmisc/ListOfTables.vue";

export default {
    components: {
        "list-of-sbases": ListOfSBases,
        "list-of-tables": ListOfTables,
    },
};
</script>

<style lang="scss" scoped>
.tab-container {
    display: flex;
    flex-direction: column;
    height: 75vh;
}
</style>
