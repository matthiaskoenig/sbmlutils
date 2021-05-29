<template>
    <div class="hello">
        <h1>{{ msg }}</h1>

        <h3>Essential Links</h3>
        <ul>
            <li>
                <a href="https://https://github.com/matthiaskoenig/sbmlutils" target="_blank" rel="noopener">sbmlutils</a>
            </li>
            <li>
                <a href="http://sbml.org" target="_blank" rel="noopener">SBML</a>
            </li>
            <li>
                <a href="https://summerofcode.withgoogle.com/projects/#5355377035575296" target="_blank" rel="noopener">Project Description</a>
            </li>
        </ul>
    </div>
</template>

<script lang="ts">
import { Options, Vue } from "vue-class-component";

@Options({
    props: {
        msg: String,
    },
})
export default class HelloWorld extends Vue {
    msg!: string;
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
    @import '../assets/styles/scss/components/HelloWorld.scss';
</style>
