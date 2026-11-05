import java.io.*;
import java.nio.file.*;
import java.util.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

/** Observe actual metadata and neighbour eligibility INSIDE surrogate calculations. */
public class JidtSurrogateAudit {
  static int[] expected;static PrintWriter out;static String context;
  static void capture(int[] times,int[] sets,KdTree tree)throws Exception{
    boolean exact=Arrays.equals(times,expected),same=true;for(int id:sets)if(id!=0)same=false;
    boolean[] mask=new boolean[times.length];tree.findPointsWithinR(79,Double.POSITIVE_INFINITY,45,true,mask,new int[times.length+1]);
    int[] separation={44,45,46};
    for(int delta:separation){int j=Arrays.binarySearch(expected,79+delta);out.println(context+","+exact+","+same+","+delta+","+(delta>45)+","+mask[j]);}
  }
  static class MI extends MutualInfoCalculatorMultiVariateKraskov1 {
    protected double[] computeFromObservations(boolean locals,double[][][] fresh)throws Exception{ensureKdTreesConstructed();capture(getObservationTimePoints(),getObservationSetIndices(),kdTreeJoint);return super.computeFromObservations(locals,fresh);}
  }
  static class CMI extends ConditionalMutualInfoCalculatorMultiVariateKraskov1 {
    protected double[] computeFromObservations(boolean locals,double[][][] fresh)throws Exception{ensureKdTreesConstructed();capture(getObservationTimePoints(),getObservationSetIndices(),kdTreeJoint);return super.computeFromObservations(locals,fresh);}
  }
  public static void main(String[] args)throws Exception{
    int n=240;expected=new int[n];double[][] x=new double[n][1],y=new double[n][1],z=new double[n][1];int[] order=new int[n];Random random=new Random(117);
    for(int i=0;i<n;i++){expected[i]=i<80?i:i<160?i+10:i+80;x[i][0]=random.nextGaussian();y[i][0]=random.nextGaussian();z[i][0]=random.nextGaussian();order[i]=n-1-i;}
    try(PrintWriter writer=new PrintWriter(args[0])){
      out=writer;out.println("calculation,time_indices_exact,same_set_id,elapsed_separation,expected_eligible,actual_eligible");
      MI mi=new MI();SharedEstimatorSettings.apply(mi);ElapsedHourLoader.load(mi,expected,x,y,4,45);context="mi_observed";mi.computeAverageLocalOfObservations();
      context="mi_computeSignificance_wrapper";mi.computeSignificance(new int[][]{order});
      context="mi_single_reordering";mi.computeAverageLocalOfObservations(order);
      CMI cmi=new CMI();SharedEstimatorSettings.apply(cmi);ElapsedHourLoader.load(cmi,expected,x,y,z,4,45);context="cmi_observed";cmi.computeAverageLocalOfObservations();
      context="cmi_computeSignificance_wrapper";cmi.computeSignificance(1,new int[][]{order});
      context="cmi_single_reordering";cmi.computeAverageLocalOfObservations(1,order);
      ElapsedHourLoader.verify(expected,mi.getObservationTimePoints(),mi.getObservationSetIndices(),mi.getNumObservations());
      ElapsedHourLoader.verify(expected,cmi.getObservationTimePoints(),cmi.getObservationSetIndices(),cmi.getNumObservations());
    }
  }
}
