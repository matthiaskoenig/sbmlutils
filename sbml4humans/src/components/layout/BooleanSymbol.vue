<template>
    <div class="symbol">
        <i class="fa fa-check-circle" v-if="value" style="color: green"></i>

        <i class="fa fa-times-circle" v-else-if="!value" style="color: red"></i>

        <i class="fa fa-ban black" v-else></i>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";

export default defineComponent({
    props: {
        value: {
            type: Boolean,
            default: false,
        },
    },
});
</script>

<style lang="scss" scoped>
.symbol {
    display: inline-flex;
    margin: 0px 5px;
}
</style>
