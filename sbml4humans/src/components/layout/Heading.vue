<template>
    <strong>
        <i :class="`fas fa-${icon} p-mr-1`" />
        {{
            isTable
                ? "ListOf" + (sbmlType === "Species" ? sbmlType : sbmlType + "s")
                : sbmlType
        }}
    </strong>
</template>

<script lang="ts">
import icons from "@/data/fontAwesome";
import { defineComponent } from "vue";

export default defineComponent({
    props: {
        sbmlType: {
            type: String,
            default: "SBMLDocument",
        },

        isTable: {
            type: Boolean,
            default: false,
        },
    },

    computed: {
        icon(): string {
            return icons.icons[this.sbmlType];
        },
    },
});
</script>
