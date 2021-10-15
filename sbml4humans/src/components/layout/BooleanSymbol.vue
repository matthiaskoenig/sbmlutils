<template>
    <div class="symbol">
        <span v-if="value">
            <font-awesome-icon
                icon="check-square"
                title="true"
                style="color: black; font-size: 13px"
            />
        </span>
        <span v-else-if="!value">
            <font-awesome-icon
                icon="square"
                title="false"
                style="color: darkgrey;  font-size: 13px"
            />
        </span>
        <span v-else>
            <font-awesome-icon icon="ban black" style="color: black; font-size: 13px" />
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
