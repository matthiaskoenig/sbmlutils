<template>
    <div class="symbol">
        <span v-if="value">
            <font-awesome-icon
                icon="check-circle"
                style="color: green; font-size: 14px"
            />
        </span>
        <span v-else-if="!value">
            <font-awesome-icon
                icon="times-circle"
                style="color: red; font-size: 14px"
            />
        </span>
        <span v-else>
            <font-awesome-icon icon="ban black" style="color: red; font-size: 14px" />
        </span>
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
    margin-top: 2px;
}
</style>
