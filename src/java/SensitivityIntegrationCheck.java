import java.nio.file.*;
import java.io.*;
import java.util.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

/** Actual joint/marginal neighbour checks for hourly and half-hourly indexing. */
public final class SensitivityIntegrationCheck {
  static class MI extends MutualInfoCalculatorMultiVariateKraskov1 {
    NearestNeighbourSearcher[] searches()throws Exception{ensureKdTreesConstructed();return new NearestNeighbourSearcher[]{kdTreeJoint,nnSearcherSource,nnSearcherDest};}
    KdTree tree()throws Exception{ensureKdTreesConstructed();return kdTreeJoint;}
  }
  static class CMI extends ConditionalMutualInfoCalculatorMultiVariateKraskov1 {
    NearestNeighbourSearcher[] searches()throws Exception{ensureKdTreesConstructed();return new NearestNeighbourSearcher[]{kdTreeJoint,kdTreeVar1Conditional,uniNNSearcherVar1,kdTreeVar2Conditional,uniNNSearcherVar2,nnSearcherConditional};}
    KdTree tree()throws Exception{ensureKdTreesConstructed();return kdTreeJoint;}
    void dims(int d){check(dimensionsVar1==d&&dimensionsVar2==1&&dimensionsCond==1,"Wrong CMI dimensions");}
  }
  static void check(boolean x,String message){if(!x)throw new AssertionError(message);}
  static void masks(KdTree tree,NearestNeighbourSearcher[] searches,int[] times,int window,int k)throws Exception{
    for(int i=0;i<times.length;i++){
      boolean[] actual=new boolean[times.length];tree.findPointsWithinR(i,Double.POSITIVE_INFINITY,window,true,actual,new int[times.length+1]);int count=0;
      for(int j=0;j<times.length;j++){boolean expected=Math.abs(times[i]-times[j])>window;check(actual[j]==expected,"Exact-time eligibility mismatch");if(expected)count++;}
      for(NearestNeighbourSearcher s:searches)if(s!=null)check(s.countPointsWithinR(i,Double.POSITIVE_INFINITY,window,true)==count,"Marginal eligibility mismatch");
      PriorityQueue<NeighbourNodeData> nn=tree.findKNearestNeighbours(k,i,window);check(nn.size()==k,"Wrong neighbour count");for(NeighbourNodeData p:nn)check(Math.abs(times[p.sampleIndex]-times[i])>window,"Within-window nearest neighbour");
    }
  }
  public static void main(String[] args)throws Exception{
    try(PrintWriter out=new PrintWriter(args[0])){
      out.println("index_unit_hours,window_hours,window_ticks,k,n,mi_pass,period_cmi_pass,direction_cmi_pass,boundary_and_gap_masks_pass");
      for(int units:new int[]{1,2}){
        ArrayList<Integer> list=new ArrayList<>();for(int t=0;t<320*units;t++)if(!(t>=80*units&&t<90*units)&&!(t>=170*units&&t<240*units))list.add(t);
        int n=list.size();int[] times=list.stream().mapToInt(Integer::intValue).toArray();Random rng=new Random(20261031);
        double[][] ho=new double[n][1],hn=new double[n][1],tp=new double[n][1],dir=new double[n][2];
        for(int i=0;i<n;i++){ho[i][0]=rng.nextGaussian();hn[i][0]=.5*ho[i][0]+rng.nextGaussian();tp[i][0]=rng.nextGaussian();double theta=rng.nextDouble()*6.28;dir[i][0]=Math.cos(theta);dir[i][1]=Math.sin(theta);}
        for(int w:new int[]{30,45,60})for(int k:new int[]{3,4,6,8}){
          if(k!=4&&w!=45)continue;int ticks=SensitivitySettings.windowTicks(w,1.0/units);
          MI mi=new MI();SharedEstimatorSettings.apply(mi);ElapsedHourLoader.load(mi,times,ho,hn,k,ticks);SensitivitySettings.verify(mi,k,ticks);
          CMI period=new CMI();SharedEstimatorSettings.apply(period);ElapsedHourLoader.load(period,times,tp,hn,ho,k,ticks);SensitivitySettings.verify(period,k,ticks);period.dims(1);
          CMI direction=new CMI();SharedEstimatorSettings.apply(direction);ElapsedHourLoader.load(direction,times,dir,hn,ho,k,ticks);SensitivitySettings.verify(direction,k,ticks);direction.dims(2);
          masks(mi.tree(),mi.searches(),times,ticks,k);masks(period.tree(),period.searches(),times,ticks,k);masks(direction.tree(),direction.searches(),times,ticks,k);
          check(Double.isFinite(mi.computeAverageLocalOfObservations())&&Double.isFinite(period.computeAverageLocalOfObservations())&&Double.isFinite(direction.computeAverageLocalOfObservations()),"Estimator failed");
          out.println((1.0/units)+","+w+","+ticks+","+k+","+n+",true,true,true,true");
        }
      }
    }
  }
}
