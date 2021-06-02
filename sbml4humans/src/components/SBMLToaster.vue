<template>

</template>

<script>
import colors from "@/data/colorScheme";

export default {
    props: {
        sid: String,
        name: String,
        sbmlType: String,
    },

    data() {
        return {
            color: String,
        };
    },

    mounted() {
        this.color = colors.componentColor[this.sbmlType]
            ? colors.componentColor[this.sbmlType]
            : colors.componentColor.Default;
    },
}
</script>

<style lang="scss" scoped>

</style>
