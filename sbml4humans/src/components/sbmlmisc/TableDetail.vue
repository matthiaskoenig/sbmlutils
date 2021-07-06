<template>
    <div class="table-container">
        <h1 class="sbmlType px-2 py-1" v-bind:style="`background-color: ${color}`">
            ListOf{{ sbmlType === "Species" ? sbmlType : sbmlType + "s" }}
        </h1>

        <table class="table table-striped table-bordered">
            <thead class="thead-dark">
                <tr>
                    <th scope="col">Sr.No.</th>
                    <th scope="col">{{ sbmlType }}</th>
                </tr>
            </thead>
            <tbody class="table-body">
                <tr v-for="(pk, index) in info.objects" v-bind:key="pk">
                    <td>{{ index + 1 }}</td>
                    <td>
                        <span class="links" v-on:click="openComponent(pk)">{{
                            pk
                        }}</span>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import colorScheme from "@/data/colorScheme";
import { defineComponent } from "vue";

export default defineComponent({
    props: {
        sbmlType: {
            type: String,
            default: "SBMLDocument",
        },
        info: {
            type: Object,
        },
    },

    methods: {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
        },
    },

    computed: {
        color(): string {
            return colorScheme.componentColor[this.sbmlType];
        },
    },
});
</script>

<style lang="scss" scoped>
.sbmlType {
    width: fit-content;
}

.table {
    text-align: center;
}


</style>
